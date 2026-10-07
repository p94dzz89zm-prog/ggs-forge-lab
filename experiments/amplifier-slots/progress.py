"""Bounded progressive experiment; never expand through a failed gate."""
import json,subprocess,sys,time,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots'
with (OUT/'checkpoint-watch.log').open('a') as f:
 subprocess.Popen([sys.executable,str(HERE/'checkpoint_watch.py')],cwd=WORK,stdout=f,stderr=subprocess.STDOUT)
def run(script,*args,log):
 with (OUT/log).open('a') as f:subprocess.run([sys.executable,str(HERE/script),*map(str,args)],cwd=WORK,stdout=f,stderr=subprocess.STDOUT,check=True)
parser=argparse.ArgumentParser();parser.add_argument('--resume-gate',action='store_true');args=parser.parse_args()
if args.resume_gate and not (OUT/'gate/performance.json').exists():run('run_batch.py','--gate','--resume','--seed',202610060,'--seeds',1,'--out',OUT/'gate',log='gate-progress-resumed.log')
while not (OUT/'gate/performance.json').exists():time.sleep(5)
g=json.loads((OUT/'gate/performance.json').read_text());assert g['valid']==28 and g['attempted']==28
if not (OUT/'gate-receipt.json').exists():run('check_gate.py',OUT/'gate',log='gate-check.log')
run('checkpoint.py',OUT/'gate',log='gate-save-final.log')
print('Gate and baseline replay passed; experimental collection begins',flush=True)
deadline=json.loads((OUT/'deadline-gate-receipt.json').read_text());assert deadline['passed'] and deadline['games']==16
concurrency=json.loads((OUT/'concurrency-gate-receipt.json').read_text());assert concurrency['passed'] and concurrency['games']==16 and concurrency['workers_after']==2
arms=[x['name'] for x in json.loads((HERE/'protocol.json').read_text())['arms']]
for target,seed,seeds in [(16,202610061,4),(32,202610065,4),(64,202610069,8),(96,202610077,8),(128,202610085,8)]:
 if target>64:
  r=json.loads((OUT/'Pure_GGS_Amplifier_Results.json').read_text());arms=[a['name'] for a in r['arms'] if not a['stability']['passed'] and a['valid']<target]
  if not arms:break
 stage=OUT/f'stage-{target:03d}'
 perf=json.loads((stage/'performance.json').read_text()) if (stage/'performance.json').exists() else {}
 if perf.get('valid')!=seeds*4*len(arms):
  print('Starting cumulative stage',target,'arms',arms,flush=True)
  run('run_batch.py','--seed',seed,'--seeds',seeds,'--out',stage,'--arms',*arms,'--timeout',600,'--workers',2,*(['--resume'] if stage.exists() else []),log=f'stage-{target:03d}-progress.log')
 run('compare.py','--through-stage',target,log=f'comparison-{target:03d}.log');r=json.loads((OUT/'Pure_GGS_Amplifier_Results.json').read_text());assert not r['unresolved_exclusions'],'Pause: excluded game requires audit'
 (OUT/f'comparison-{target:03d}.json').write_text(json.dumps({k:v for k,v in r.items() if k not in ['games','reused_baseline_games','baseline_exposure']},indent=2)+'\n')
 run('cleanup_saved.py',log=f'cleanup-{target:03d}.log')
 print('Stage completed',target,'new valid',r['valid'],'stable',[a['name'] for a in r['arms'] if a['stability']['passed']],flush=True)
(OUT/'collection-completed.json').write_text(json.dumps({'valid':r['valid'],'arms':[(a['name'],a['valid'],a['stability']['passed']) for a in r['arms']]},indent=2)+'\n')
print('Collection completed',flush=True)
run('finish.py',log='final-deliverables.log')
