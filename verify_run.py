"""Offline raw-receipt reconstruction, independent of runner classification."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import regex
import verify
ROOT=Path(__file__).resolve().parent
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');a=ap.parse_args();run=Path(a.run)
    verify.main();schedule=read(ROOT/'schedules/pilot.json');meta=read(run/'run.json');end=read(run/'complete.json')
    assert meta['protocol_sha256']==digest(ROOT/'protocol.json')
    assert meta['schedule_sha256']==digest(ROOT/'schedules/pilot.json')
    previous='0'*64;counts={c:collections.Counter() for c in 'ABCDEFGH'};rows=[];cost=0
    folders=sorted(run.glob('pilot-*'));assert len(folders)==end['executed']
    for i,folder in enumerate(folders):
        event=read(folder/'event.json');out=read(folder/'classification.json');slot=schedule[i]
        assert folder.name==slot['slot_id'] and event['slot']==slot
        assert event['previous_event_sha256']==previous
        for name in ('request','response','classification'):
            file=folder/(name+('.json' if name=='classification' else '.bin'))
            assert event[name+'_sha256']==digest(file)
        assert (folder/'request.bin').read_bytes()==(ROOT/'requests'/(slot['cell']+'.json')).read_bytes()
        previous=digest(folder/'event.json')
        if out['class']!='ERROR':
            assert event['http_status']==200
            raw=read(folder/'response.bin');assert len(raw['choices'])==1
            choice=raw['choices'][0];m=choice['message'];text=m.get('content');finish=choice['finish_reason']
            assert m['role']=='assistant' and (text is None or type(text)==str)
            if finish=='content_filter': expected='SAFETY'
            elif m.get('refusal'): expected='REFUSAL'
            elif m.get('tool_calls') or m.get('function_call') or finish in ('tool_calls','function_call'): expected='TOOL'
            elif text is None or text=='':
                expected={'stop':'V0' if text=='' else 'V2','length':'V1','other':'VU'}[finish]
            else:
                matches=[k for k,v in read(ROOT/'targets.json').items() if v==text]
                expected=matches[0] if matches else 'MX' if regex.search(r'\p{sc=Arabic}',text) and regex.search(r'\p{sc=Hebrew}',text) else 'OT'
            assert out['class']==expected and out['answer']==text and out['answer_bytes']==len((text or '').encode())
            assert out['usage']==raw.get('usage') and out['model']==raw.get('model')
            assert out['reasoning_bytes']==(None if m.get('reasoning_content') is None else len(m['reasoning_content'].encode()))
        if event['cost_upper_usd'] is not None:
            u=out['usage'];assert abs(event['cost_upper_usd']-(u['prompt_tokens']*6+u['completion_tokens']*15)/1e6)<1e-10
        cost+=event['reserved_usd'] if event['cost_upper_usd'] is None else event['cost_upper_usd']
        assert abs(cost-event['cumulative_upper_usd'])<1e-10
        counts[slot['cell']][out['class']]+=1
        rows.append({'slot':slot['slot_id'],'cell':slot['cell'],**out})
    assert previous==end['last_event_sha256'] and abs(cost-end['cost_upper_usd'])<1e-10
    assert cost<=meta['budget_usd'] and end['unexecuted']==40-len(folders)
    if end['status']=='COMPLETE': assert len(folders)==40
    result={'verification':'PASS','status':end['status'],'inference':'COMPLETE' if len(folders)==40 else 'INCONCLUSIVE','executed':len(folders),'scheduled':40,'counts':counts,'cost_upper_usd':cost,'rows':rows}
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__': main()
