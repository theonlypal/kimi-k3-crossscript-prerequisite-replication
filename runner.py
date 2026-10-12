"""Serial pilot executor. No retries, fallback, or payload mutation."""
import argparse
import datetime
import hashlib
import http.client
import json
from pathlib import Path
import subprocess
import sys
import regex
import verify

ROOT = Path(__file__).resolve().parent
def encode(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def save(p,x): p.write_bytes(encode(x)+b'\n')
def read(p): return json.loads(p.read_bytes())
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def pairs(items):
    d={}
    for k,v in items:
        if k in d: raise ValueError('duplicate JSON key')
        d[k]=v
    return d
def strict(b):
    return json.loads(b, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite')))

def classify(status,raw):
    out={'class':'ERROR'}
    try:
        d=strict(raw)
        if status != 200 or not isinstance(d,dict) or d.get('error'): return out
        cs=d.get('choices')
        if not isinstance(cs,list) or len(cs)!=1: return out
        c=cs[0]; m=c['message']; f=c.get('finish_reason')
        if not isinstance(m,dict) or m.get('role')!='assistant': return out
        text=m.get('content'); reasoning=m.get('reasoning_content')
        if text is not None and not isinstance(text,str): return out
        if reasoning is not None and not isinstance(reasoning,str): return out
        out.update(model=d.get('model'),response_id=d.get('id'),finish_reason=f,
                   content_state='missing' if 'content' not in m else 'null' if text is None else 'string',
                   answer=text,answer_bytes=len((text or '').encode()),
                   reasoning_state='missing' if 'reasoning_content' not in m else 'null' if reasoning is None else 'string',
                   reasoning_bytes=None if reasoning is None else len(reasoning.encode()),usage=d.get('usage'))
        if f=='content_filter': out['class']='SAFETY'
        elif m.get('refusal'): out['class']='REFUSAL'
        elif m.get('tool_calls') or m.get('function_call') or f in ('tool_calls','function_call'): out['class']='TOOL'
        elif f not in ('stop','length','other'): return out
        elif not text: out['class']=('V0' if isinstance(text,str) else 'V2') if f=='stop' else 'V1' if f=='length' else 'VU'
        else:
            targets=read(ROOT/'targets.json')
            out['class']=next((k for k,v in targets.items() if text==v),None) or ('MX' if regex.search(r'\p{Script=Arabic}',text) and regex.search(r'\p{Script=Hebrew}',text) else 'OT')
        return out
    except (ValueError,KeyError,TypeError,UnicodeError): return {'class':'ERROR'}

def request(key,method,path,body=None):
    c=http.client.HTTPSConnection('api.moonshot.ai',timeout=600)
    try:
        c.request(method,path,body=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        r=c.getresponse(); return r.status,list(r.getheaders()),r.read()
    finally: c.close()

def balance(key):
    status,headers,raw=request(key,'GET','/v1/users/me/balance')
    d=strict(raw)
    assert status==200 and d['code']==0 and d['status'] is True
    amount=d['data']['available_balance']
    assert isinstance(amount,(float,int)) and amount>0
    return float(amount)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key-file',required=True);ap.add_argument('--output',required=True);ap.add_argument('--public-commit',required=True);args=ap.parse_args()
    verify.main()
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert commit==args.public_commit
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','tag','--points-at','HEAD'],cwd=ROOT,text=True).strip()
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]
    assert remote==commit
    dest=Path(args.output).resolve(); assert dest.parent==ROOT/'runs' and not dest.exists()
    key=Path(args.key_file).read_text().strip()
    available=balance(key); ceiling=min(available,2.5)
    schedule=read(ROOT/'schedules/pilot.json'); protocol=read(ROOT/'protocol.json')
    dest.mkdir(parents=True)
    # Input allowance uses request byte count plus 4096 tokens of framing reserve.
    # All input charged at uncached input + default cache write: $6/M.
    # Completion tokens include reasoning; $15/M. No cache discount assumed.
    save(dest/'run.json',{'started':now(),'commit':commit,'phase':'pilot','available_balance_usd':available,'budget_usd':ceiling,'input_upper_usd_per_million':6,'output_usd_per_million':15,'protocol_sha256':sha((ROOT/'protocol.json').read_bytes()),'schedule_sha256':sha((ROOT/'schedules/pilot.json').read_bytes())})
    previous='0'*64; charged=0.;model=None;reason='COMPLETE';completed=0
    for slot in schedule:
        verify.main()
        body=(ROOT/'requests'/(slot['cell']+'.json')).read_bytes(); assert sha(body)==slot['request_sha256']
        input_allowance=len(body)+4096
        reserve=(input_allowance*6+8192*15)/1000000
        if charged+reserve>ceiling: reason='BUDGET';break
        folder=dest/slot['slot_id'];folder.mkdir();(folder/'request.bin').write_bytes(body)
        started=now();status=None;headers=[];raw=b'';transport=None
        try: status,headers,raw=request(key,'POST','/v1/chat/completions',body)
        except Exception as e: transport=type(e).__name__
        (folder/'response.bin').write_bytes(raw)
        outcome=classify(status,raw);save(folder/'classification.json',outcome)
        actual=None;usage=outcome.get('usage')
        if isinstance(usage,dict):
            pt=usage.get('prompt_tokens');ct=usage.get('completion_tokens')
            if type(pt)==int and type(ct)==int and 0<=pt<=input_allowance and 0<=ct<=8192:
                actual=(pt*6+ct*15)/1000000
        charged+=reserve if actual is None else actual
        event={'slot':slot,'started':started,'ended':now(),'http_status':status,'headers':headers,'transport_error':transport,'request_sha256':sha(body),'response_sha256':sha(raw),'classification_sha256':sha((folder/'classification.json').read_bytes()),'reserved_usd':reserve,'cost_upper_usd':actual,'cumulative_upper_usd':charged,'previous_event_sha256':previous}
        save(folder/'event.json',event);previous=sha((folder/'event.json').read_bytes());completed+=1
        print(json.dumps({'slot':slot['slot_id'],'cell':slot['cell'],'http':status,'class':outcome['class'],'answer':outcome.get('answer'),'bytes':outcome.get('answer_bytes'),'finish':outcome.get('finish_reason'),'cost_upper_usd':round(charged,6)},ensure_ascii=False),flush=True)
        if outcome['class']=='ERROR': reason='ERROR';break
        returned=outcome.get('model')
        if not isinstance(returned,str) or not returned or (model is not None and returned!=model): reason='MODEL_ID';break
        model=returned
        if actual is None: reason='USAGE';break
    save(dest/'complete.json',{'ended':now(),'status':reason,'executed':completed,'scheduled':40,'unexecuted':40-completed,'last_event_sha256':previous,'cost_upper_usd':charged,'budget_usd':ceiling})
    print(json.dumps(read(dest/'complete.json')),flush=True)
if __name__=='__main__': main()
