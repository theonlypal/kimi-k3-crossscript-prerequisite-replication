"""One-time offline native request construction; no credentials or inference."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def encoded(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(x):
    return hashlib.sha256(x).hexdigest()
def save(p,x):
    p.write_bytes(encoded(x)+b'\n')

def build():
    if (ROOT/'freeze_manifest.json').exists():
        raise SystemExit('Already frozen; use verify.py')
    prompts=json.loads((ROOT/'prompts.json').read_bytes())
    cells=dict(A=['S1','P1'],B=['S1','P0'],C=['S_no_rule','P1'],D=['S_no_rule','P0'],E=['S1','P1'],F=['S1','P0'],G=['S_reassigned','P1'],H=['S_reassigned','P0'])
    protocol={'author':'Rayan Pal','date':'2026-10-12','version':'1.0.0','model':'kimi-k3','endpoint':'https://api.moonshot.ai/v1/chat/completions','max_completion_tokens':8192,'reasoning_effort':'low','stream':False,'concurrency':1,'automatic_retries':0,'timeout_seconds':600,'cells':cells,'primary':'NSTOP = V0 + V2','pilot_budget_usd':2.5,'omitted':['temperature','top_p','seed','stop','tools','tool_choice','response_format','prompt_cache_key','prompt_cache_options','thinking'],'phases':{'pilot':{'n_per_cell':5,'seed':'rayan-pal-gemini3-crossscript-pilot-2026-10-12'},'confirmatory':{'n_per_cell':200,'seed':'rayan-pal-gemini3-crossscript-confirmatory-2026-10-12'}},'source_commit':'a3141b05676b70e90a358c05cfc7b70f8f41ff86','authorization':'Separate explicit phase authorization required; no live execution authorized by publication.','budget_policy':'Verified balance and current rates required before execution. Reserve full next-request cost; stop before exceeding lower of verified balance and 2.50 USD. No top-up, retries or cap changes. Missing trials remain missing.'}
    save(ROOT/'protocol.json',protocol)
    (ROOT/'requests').mkdir(); (ROOT/'schedules').mkdir()
    for c,(s,u) in cells.items():
        body={'model':'kimi-k3','messages':[{'role':'system','content':prompts[s]},{'role':'user','content':prompts[u]}],'max_completion_tokens':8192,'reasoning_effort':'low','stream':False}
        (ROOT/'requests'/(c+'.json')).write_bytes(encoded(body))
    for phase,spec in protocol['phases'].items():
        rows=[{'cell':c,'repetition':i} for c in cells for i in range(1,spec['n_per_cell']+1)]
        rows.sort(key=lambda r:(sha((spec['seed']+'|'+r['cell']+'|'+str(r['repetition'])).encode()),r['cell'],r['repetition']))
        for i,r in enumerate(rows,1):
            r.update(slot_id='%s-%04d'%(phase,i),request_sha256=sha((ROOT/'requests'/(r['cell']+'.json')).read_bytes()))
        save(ROOT/'schedules'/(phase+'.json'),rows)
    files={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}
    save(ROOT/'freeze_manifest.json',{'version':'1.0.0','tag':'v1.0.0-preregistered','files':files})
    (ROOT/'SHA256SUMS.txt').write_text(''.join(h+'  '+n+'\n' for n,h in files.items())+sha((ROOT/'freeze_manifest.json').read_bytes())+'  freeze_manifest.json\n')
    print('Frozen offline: 40 pilot and 1600 confirmatory requests. No model calls.')
if __name__=='__main__':
    build()
