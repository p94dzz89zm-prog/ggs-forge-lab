"""Finish restored stage128 with a single collector and durable four-game checkpoints.

Never rerun saved identities. Collection and final reanalysis are separate so
an interruption during analysis does not launch another collector.
"""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('--analysis-only',action='store_true');a=p.parse_args()
batch=WORK/'truly-pure-comparison/stage-128';summary=batch/'summary.json'
def rows():return json.loads(summary.read_text())
def command(script,*args):return [sys.executable,str(HERE/script),*map(str,args)]
def checkpoint():subprocess.run(command('checkpoint.py','--batch',batch),check=True)
if not a.analysis_only:
 before=rows();assert all(r['status']=='completed' for r in before)
 progress=WORK/'truly-pure-comparison/finish-progress.log'
 with progress.open('a',buffering=1) as output:
  proc=subprocess.Popen(command('run.py','--out',batch,'--seed',202610226,'--seeds',8,'--resume'),stdout=output,stderr=subprocess.STDOUT)
  saved=len(before)
  while proc.poll() is None:
   current=rows()
   if any(r['status']!='completed' for r in current):
    proc.wait();raise SystemExit('Invalid attempt retained; investigate before any retry')
   if len(current)>=saved+4:checkpoint();saved=len(current)
   time.sleep(5)
  if proc.returncode:raise SystemExit(f'Collector stopped with status {proc.returncode}; inspect progress and raw attempts')
 checkpoint()
assert len(rows())==64 and all(r['status']=='completed' for r in rows())
root=WORK/'truly-pure-comparison'
subprocess.run(command('compare.py',*[root/f'stage-{s:03}' for s in (32,64,96,128)],'--out',root/'comparison-128.json'),check=True)
print('All256 production games collected, saved and uniformly reanalysed',flush=True)
