"""Frozen, paired actual-Forge collection. No deck changes and no automatic retry."""
import argparse, gzip, hashlib, importlib.util, json, shutil, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; WORK=ROOT.parent
sys.path.insert(0,str(ROOT)); import dragonmind
from measure import extract as supplement
spec=importlib.util.spec_from_file_location('observed',ROOT/'experiments/pure-ggs/analyze.py'); observed=importlib.util.module_from_spec(spec);spec.loader.exec_module(observed)
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
protocol=json.loads((Path(__file__).parent/'protocol.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,h in protocol['deck_sha256'].items(): assert sha(ROOT/'decks'/f'{n}.dck')==h
jar=WORK/'decision-clock-probe/engine-decision-clock.jar';assert sha(jar)==protocol['engine_sha256']
out=a.out.resolve();out.mkdir(parents=True,exist_ok=a.resume);(out/'analysis').mkdir(exist_ok=a.resume)
def atomic(name,obj):
 t=out/(name+'.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(out/name)
metadata={'protocol':protocol,'seed':a.seed,'seeds':a.seeds,'workers':2,'timeout':600}
if (out/'metadata.json').exists():assert json.loads((out/'metadata.json').read_text())==metadata
else:atomic('metadata.json',metadata)
rows=json.loads((out/'summary.json').read_text()) if (out/'summary.json').exists() else []
assert all(r['status']=='completed' for r in rows),'Investigate invalid attempts before resuming'
done={(r['variant'],r['seed'],r['seat_rotation']) for r in rows}
jobs=[(d,s,r) for s in range(a.seed,a.seed+a.seeds) for r in range(4) for d in protocol['arms'] if (d,s,r) not in done]
def work(job):
 d,s,r=job;rs=dragonmind.batch(WORK/'restored-v28/engine',jar,out,d,r,[s],600,True,True,extra_jvm_flags=('-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.casualSeven=true','-Ddragonmind.aiDecisionTimeoutSeconds=30'))
 for row in rs:
  if row['status']!='completed':continue
  m,t=observed.extract(out,row);m['variant']=d
  (out/'analysis'/f'{d}-{s}-r{r}-metrics.json').write_text(json.dumps(m,indent=2)+'\n')
  with gzip.open(out/'analysis'/f'{d}-{s}-r{r}-timeline.json.gz','wt') as f:json.dump(t,f)
  if m['measurement_gaps'] or m['snapshot_life_match_rate']!=1:row['status']='measurement_error';row['measurement_gaps']=m['measurement_gaps']
  for audit in (out/'audit'/Path(row['log']).stem).glob('*.jsonl'):
   dest=audit.with_suffix('.jsonl.gz')
   with audit.open('rb') as src,gzip.open(dest,'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
   with gzip.open(dest,'rb') as f:
    while f.read(1<<20):pass
   audit.unlink()
  extended=supplement(out,row,m,t)
  (out/'analysis'/f'{d}-{s}-r{r}-extended.json').write_text(json.dumps(extended,indent=2)+'\n')
 return rs
start=time.monotonic()
for rs in dragonmind.run_jobs(jobs,work,2,True):
 rows+=rs;atomic('summary.json',rows);print(json.dumps({'games':len(rows),'last':[(r['variant'],r['seed'],r['seat_rotation'],r['status']) for r in rs],'seconds':round(time.monotonic()-start,1)}),flush=True)
if any(r['status']!='completed' for r in rows):raise SystemExit('Reliability failed; collection paused')
