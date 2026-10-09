"""Sequential gated collection, durable completed evidence, and cumulative analysis."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'truly-pure-comparison'
def run(script,*args):subprocess.run([sys.executable,str(HERE/script),*map(str,args)],check=True,cwd=WORK)
gate=OUT/'gate'
while True:
 if (gate/'summary.json').exists():
  rows=json.loads((gate/'summary.json').read_text())
  if any(r['status']!='completed' for r in rows):raise SystemExit('Gate failed; investigate before collecting deck-performance data')
  if len(rows)==16:break
 time.sleep(5)
run('check_gate.py',gate);run('checkpoint.py','--batch',gate)
batches=[]
for i,total in enumerate((32,64,96,128)):
 batch=OUT/f'stage-{total:03}';log=OUT/f'stage-{total:03}-progress.log';batches.append(batch)
 assert not batch.exists(),'Existing stage requires explicit audited resume, not overwrite'
 with log.open('w') as stream:
  proc=subprocess.Popen([sys.executable,str(HERE/'run.py'),'--out',str(batch),'--seed',str(202610202+i*8),'--seeds','8'],cwd=WORK,stdout=stream,stderr=subprocess.STDOUT)
  last_saved=0
  while proc.poll() is None:
   if (batch/'summary.json').exists():
    rows=json.loads((batch/'summary.json').read_text());count=sum(r['status']=='completed' for r in rows)
    if count>=last_saved+8:run('checkpoint.py','--batch',batch);last_saved=count
   time.sleep(10)
  if proc.returncode:raise SystemExit(f'Collection paused in {batch.name}; preserve invalid attempt and investigate')
 run('checkpoint.py','--batch',batch);run('compare.py',*batches,'--out',OUT/f'comparison-{total:03}.json')
 (OUT/'progression.json').write_text(json.dumps({'complete_games_per_arm':total,'batches':[str(b) for b in batches],'decks_unchanged':True,'final_collection_complete':total==128},indent=2)+'\n')
 print(f'Completed controlled stage: {total} valid games per deck',flush=True)
