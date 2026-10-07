import argparse,gzip,hashlib,importlib.util,json,shutil,sys,time
from checkpoint import save
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));import dragonmind
spec=importlib.util.spec_from_file_location('pure_metrics',ROOT/'experiments/pure-ggs/analyze.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--seeds',type=int,required=True);p.add_argument('--arms',nargs='+');p.add_argument('--gate',action='store_true');a=p.parse_args()
protocol=json.loads((HERE/'protocol.json').read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();jar=ROOT/'experiments/pure-ggs/engine-casual-seven.jar'
assert sha(jar)==protocol['engine_sha256'] and sha(ROOT/'decks/Pure_GGS.dck')==protocol['baseline_sha256'] and sha(ROOT/'decks/GGS_Firework_Protocol_v1_0.dck')==protocol['control_sha256']
for name,value in protocol['pod_sha256'].items():assert sha(ROOT/'decks'/f'{name}.dck')==value
for arm in protocol['arms']:assert sha(ROOT/'decks'/f"{arm['name']}.dck")==arm['sha256']
arms=a.arms or (['Pure_GGS'] if a.gate else [])+[x['name'] for x in protocol['arms']]
out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);(out/'analysis').mkdir()
(out/'metadata.json').write_text(json.dumps({'protocol':protocol,'seed':a.seed,'seeds':a.seeds,'arms':arms,'gate':a.gate,'workers':4,'timeout':300,'engine_resources':'restored-v28/engine'},indent=2)+'\n')
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
   with audit.open('rb') as src,gzip.open(audit.with_suffix('.jsonl.gz'),'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
   audit.unlink()
  if m['measurement_gaps'] or m['snapshot_life_match_rate']!=1.0:row['status']='measurement_error';row['measurement_gaps']=m['measurement_gaps'];row['life_match']=m['snapshot_life_match_rate']
 return rows
jobs=[(arm,s,r) for s in range(a.seed,a.seed+a.seeds) for r in range(4) for arm in arms];rows=[];start=time.monotonic()
for rs in dragonmind.run_jobs(jobs,work,4,True):
 rows+=rs;atomic('summary.json',rows);print(json.dumps({'completed':len(rows),'requested':len(jobs),'last':[(r['variant'],r['seed'],r['seat_rotation'],r['status']) for r in rs],'wall_seconds':round(time.monotonic()-start,1)}),flush=True)
 if len(rows)//16>(len(rows)-len(rs))//16:save(out)
perf={'attempted':len(rows),'valid':sum(r['status']=='completed' for r in rows),'requested':len(jobs),'wall_seconds':round(time.monotonic()-start,3)};atomic('performance.json',perf)
save(out)
if perf['valid']!=len(jobs):raise SystemExit('Collection paused: failed reliability/integrity check')
