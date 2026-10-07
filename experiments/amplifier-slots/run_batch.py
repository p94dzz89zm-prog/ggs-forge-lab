import argparse,gzip,hashlib,importlib.util,json,shutil,sys,time
from checkpoint import save
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));import dragonmind
spec=importlib.util.spec_from_file_location('pure_metrics',ROOT/'experiments/pure-ggs/analyze.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--arms',nargs='+');p.add_argument('--gate',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args()
protocol=json.loads((HERE/'protocol.json').read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();jar=ROOT/'experiments/pure-ggs/engine-casual-seven.jar'
assert sha(jar)==protocol['engine_sha256'] and sha(ROOT/'decks/Pure_GGS.dck')==protocol['baseline_sha256'] and sha(ROOT/'decks/GGS_Firework_Protocol_v1_0.dck')==protocol['control_sha256']
for name,value in protocol['pod_sha256'].items():assert sha(ROOT/'decks'/f'{name}.dck')==value
for arm in protocol['arms']:assert sha(ROOT/'decks'/f"{arm['name']}.dck")==arm['sha256']
arms=a.arms or (['Pure_GGS'] if a.gate else [])+[x['name'] for x in protocol['arms']]
out=a.out.resolve();out.mkdir(parents=True,exist_ok=a.resume);(out/'analysis').mkdir(exist_ok=a.resume)
import fcntl
batch_lock=(out/'batch.lock').open('w');fcntl.flock(batch_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
metadata={'protocol':protocol,'seed':a.seed,'seeds':a.seeds,'arms':arms,'gate':a.gate,'workers':4,'timeout':300,'engine_resources':'restored-v28/engine'}
if (out/'metadata.json').exists():assert json.loads((out/'metadata.json').read_text())==metadata
else:(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
def atomic(name,obj):
 tmp=out/(name+'.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(out/name)
def work(job):
 arm,seed,rotation=job;rows=dragonmind.batch(ROOT.parent/'restored-v28/engine',jar,out,arm,rotation,[seed],300,True,True,extra_jvm_flags=('-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.casualSeven=true'))
 for row in rows:
  if row['status']!='completed':continue
  m,t=metrics.extract(out,row);m['variant']=arm;key=f'{arm}-{seed}-r{rotation}'
  (out/'analysis'/(key+'-metrics.json')).write_text(json.dumps(m,indent=2)+'\n')
  with gzip.open(out/'analysis'/(key+'-timeline.json.gz'),'wt',compresslevel=5) as f:json.dump(t,f,separators=(',',':'))
  for audit in (out/'audit'/Path(row['log']).stem).glob('*.jsonl'):
   compressed=audit.with_suffix('.jsonl.gz');temporary=compressed.with_suffix('.gz.tmp')
   with audit.open('rb') as src,gzip.open(temporary,'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
   with gzip.open(temporary,'rb') as check:
    while check.read(1<<20):pass
   temporary.replace(compressed);audit.unlink()
  if m['measurement_gaps'] or m['snapshot_life_match_rate']!=1.0:row['status']='measurement_error';row['measurement_gaps']=m['measurement_gaps'];row['life_match']=m['snapshot_life_match_rate']
 return rows
all_jobs=[(arm,s,r) for s in range(a.seed,a.seed+a.seeds) for r in range(4) for arm in arms]
rows=json.loads((out/'summary.json').read_text()) if a.resume and (out/'summary.json').exists() else []
assert all(r['status']=='completed' for r in rows),'Invalid attempts require investigation, not automatic retry'
done={(r['variant'],r['seed'],r['seat_rotation']) for r in rows};assert len(done)==len(rows)
assert done.issubset(set(all_jobs));jobs=[j for j in all_jobs if j not in done];start=time.monotonic()
if a.resume:
 for arm,seed,rotation in jobs:
  label=f'{arm}__seat{rotation}__seeds{seed}-{seed}';quarantine=out/'interrupted-attempts'/label
  for p in [out/(label+'.log'),out/'audit'/label,out/'runtime-home'/label,out/'engine-records'/label]:
   if p.exists():quarantine.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(quarantine/(p.parent.name+'-'+p.name)))
for rs in dragonmind.run_jobs(jobs,work,4,True):
 rows+=rs;atomic('summary.json',rows);print(json.dumps({'completed':len(rows),'requested':len(all_jobs),'last':[(r['variant'],r['seed'],r['seat_rotation'],r['status']) for r in rs],'wall_seconds':round(time.monotonic()-start,1)}),flush=True)
 if len(rows)//16>(len(rows)-len(rs))//16:save(out)
perf={'attempted':len(rows),'valid':sum(r['status']=='completed' for r in rows),'requested':len(all_jobs),'wall_seconds':round(time.monotonic()-start,3),'resumed_with':len(done)};atomic('performance.json',perf)
save(out)
if perf['valid']!=len(all_jobs):raise SystemExit('Collection paused: failed reliability/integrity check')
