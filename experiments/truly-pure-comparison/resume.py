"""Resume only verified completed rows; unchanged frozen production stages."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'truly-pure-comparison'
def run(name,*args):subprocess.run([sys.executable,str(HERE/name),*map(str,args)],check=True,cwd=WORK)
batches=[]
for i,total in enumerate((32,64,96,128)):
 batch=OUT/f'stage-{total:03}';batches.append(batch)
 existing=json.loads((batch/'summary.json').read_text()) if (batch/'summary.json').exists() else []
 if any(r['status']!='completed' for r in existing):raise SystemExit('Invalid attempt: investigate before resume')
 if len(existing)>64:raise SystemExit('Unexpected stage size')
 if len(existing)<64:
  args=[sys.executable,str(HERE/'run.py'),'--out',str(batch),'--seed',str(202610202+8*i),'--seeds','8']
  if batch.exists():args.append('--resume')
  with (OUT/f'stage-{total:03}-progress.log').open('a') as stream:
   proc=subprocess.Popen(args,cwd=WORK,stdout=stream,stderr=subprocess.STDOUT)
   saved=len(existing)
   while proc.poll() is None:
    if (batch/'summary.json').exists():
     rows=json.loads((batch/'summary.json').read_text())
     if any(r['status']!='completed' for r in rows):
      # The collector itself stops submission and lets active bounded games finish.
      proc.wait();raise SystemExit('Collection failed; preserve evidence and investigate')
     if len(rows)>=saved+4:run('checkpoint.py','--batch',batch);saved=len(rows)
    time.sleep(10)
   if proc.returncode:raise SystemExit('Collector stopped; no automatic retry')
 run('checkpoint.py','--batch',batch)
 run('compare.py',*batches,'--out',OUT/f'comparison-{total:03}.json')
 (OUT/'progression.json').write_text(json.dumps({'complete_games_per_arm':total,'final_collection_complete':total==128,'decks_unchanged':True},indent=2)+'\n')
 print('Completed controlled stage:',total,'games per deck',flush=True)
