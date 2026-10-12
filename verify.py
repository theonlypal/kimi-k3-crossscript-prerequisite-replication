"""Independent offline reconstruction of the preregistered request schedule."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_bytes())
def digest(b): return hashlib.sha256(b).hexdigest()
def main():
    manifest=read(ROOT/'freeze_manifest.json')
    for n,h in manifest['files'].items(): assert digest((ROOT/n).read_bytes())==h,n
    p=read(ROOT/'protocol.json'); prompts=read(ROOT/'prompts.json')
    for source in read(ROOT/'source_manifest.json')['sources']:
        assert digest((ROOT/source['path']).read_bytes())==source['sha256']
    for k,v in read(ROOT/'unicode_manifest.json').items():
        s=v['literal']; assert digest(s.encode())==v['sha256']; assert s.encode().hex()==v['utf8_hex']; assert len(s.encode())==v['bytes']; assert ['U+%04X'%ord(c) for c in s]==v['codepoints']
    for c,(s,u) in p['cells'].items():
        body={'model':p['model'],'messages':[{'role':'system','content':prompts[s]},{'role':'user','content':prompts[u]}],'max_completion_tokens':p['max_completion_tokens'],'reasoning_effort':p['reasoning_effort'],'stream':p['stream']}
        assert (ROOT/'requests'/(c+'.json')).read_bytes()==json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    for phase,spec in p['phases'].items():
        expected=[{'cell':c,'repetition':i} for c in p['cells'] for i in range(1,spec['n_per_cell']+1)]
        expected.sort(key=lambda r:(digest((spec['seed']+'|'+r['cell']+'|'+str(r['repetition'])).encode()),r['cell'],r['repetition']))
        for i,r in enumerate(expected,1): r.update(slot_id='%s-%04d'%(phase,i),request_sha256=digest((ROOT/'requests'/(r['cell']+'.json')).read_bytes()))
        assert expected==read(ROOT/'schedules'/(phase+'.json'))
    print(json.dumps({'status':'PASS','frozen_files':len(manifest['files']),'pilot_slots':40,'confirmatory_slots':1600,'inference_calls':0}))
if __name__=='__main__': main()
