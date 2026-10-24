#!/usr/bin/env python3
"""Refresh audited checkpoints while a separate runner is active."""
import argparse,json,subprocess,sys,time
from run_games import ROOT,make_jobs

p=argparse.ArgumentParser();p.add_argument('--output',default='thousand_games');p.add_argument('--interval',type=int,default=30);a=p.parse_args()
if not 1<=a.interval<=60:p.error('Interval must be 1–60 seconds')
folder=ROOT/a.output
metadata=json.loads((folder/'run_metadata.json').read_text());args=metadata['arguments']
manifest=json.loads((ROOT/'manifest.json').read_text())
variants=args.get('variants') or [v for v in manifest['decks'] if v.startswith('GGS_')]
target=len(make_jobs(variants,args['games_per_variant'],args['seed'],args.get('baseline_games')))
last=-1
while True:
    # Writers create records directly; ignore an in-progress partial JSON write.
    files=list((folder/'records').glob('*.json'))
    if len(files)!=last:
        try:
            for f in files:json.loads(f.read_text())
        except json.JSONDecodeError:
            time.sleep(1);continue
        for script in ('summarize.py','compare_batch.py'):
            subprocess.run([sys.executable,str(ROOT/script),'--output',a.output],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        last=len(files);print(f'Audited {last}/{target}',flush=True)
    if last==target:
        (folder/'BATCH_COMPLETE.json').write_text(json.dumps({'recorded':last,'scheduled':target,'completed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2)+'\n')
        print('All attempts audited; comparison ready.',flush=True);break
    time.sleep(a.interval)
