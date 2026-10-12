"""Export byte-preserved receipts with a separately chained public header view."""
import argparse
import hashlib
import json
from pathlib import Path

PRIVATE_HEADERS = {'set-cookie', 'cookie', 'authorization', 'proxy-authorization',
                   'msh-org-id', 'msh-project-id', 'msh-uid', 'msh-gid'}
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
def save(p,v): p.write_bytes(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()+b'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('destination');a=ap.parse_args()
    source=Path(a.source);dest=Path(a.destination)
    assert source.is_dir() and not dest.exists()
    dest.mkdir(parents=True)
    (dest/'run.json').write_bytes((source/'run.json').read_bytes())
    previous='0'*64;index=[];originals={};removed=set()
    for folder in sorted(source.glob('pilot-*')):
        target=dest/folder.name;target.mkdir()
        for n in ('request.bin','response.bin','classification.json'):
            body=(folder/n).read_bytes();(target/n).write_bytes(body)
            originals[str((target/n).relative_to(dest))]=sha(body)
        event=read(folder/'event.json')
        original_hash=sha((folder/'event.json').read_bytes())
        event['source_event_sha256']=original_hash
        event['source_previous_event_sha256']=event['previous_event_sha256']
        event['previous_event_sha256']=previous
        removed.update(k.lower() for k,v in event['headers'] if k.lower() in PRIVATE_HEADERS)
        event['headers']=[[k,v] for k,v in event['headers'] if k.lower() not in PRIVATE_HEADERS]
        save(target/'event.json',event);previous=sha((target/'event.json').read_bytes())
        m=read(target/'response.bin')['choices'][0]['message']
        assert isinstance(m['reasoning_content'],str) and isinstance(m['content'],str)
        (target/'reasoning.txt').write_bytes(m['reasoning_content'].encode())
        (target/'answer.txt').write_bytes(m['content'].encode())
        c=read(target/'classification.json')
        index.append({'slot':folder.name,'cell':event['slot']['cell'],'class':c['class'],
                      'answer':m['content'],'answer_bytes':c['answer_bytes'],
                      'response':folder.name+'/response.bin','reasoning':folder.name+'/reasoning.txt'})
    end=read(source/'complete.json')
    end['source_last_event_sha256']=end['last_event_sha256'];end['last_event_sha256']=previous
    save(dest/'complete.json',end)
    save(dest/'index.json',index)
    save(dest/'provenance.json',{'source_commit':read(source/'run.json')['commit'],
         'removed_header_names':sorted(removed),
         'transformation':'Only private response headers are removed. Public event chain recomputed; source event hashes retained. Requests, response bodies and classifications are byte-identical. Reasoning and answer text are exact decoded field bytes with no added newline.',
         'source_file_sha256':originals})
if __name__=='__main__': main()
