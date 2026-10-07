"""Replay only damaged evidence identities and four frozen baseline seats."""
import gzip,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent
sys.path.insert(0,str(ROOT));import dragonmind
spec=importlib.util.spec_from_file_location('metrics',ROOT/'experiments/pure-ggs/analyze.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
P=json.loads((HERE/'protocol.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
jar=ROOT/'experiments/pure-ggs/engine-casual-seven.jar';assert sha(jar)==P['engine_sha256']
assert sha(ROOT/'decks/Pure_GGS.dck')==P['baseline_sha256'];assert sha(ROOT/'decks/GGS_Firework_Protocol_v1_0.dck')==P['control_sha256']
for a in P['arms']:assert sha(ROOT/'decks'/f"{a['name']}.dck")==a['sha256']
for n,h in P['pod_sha256'].items():assert sha(ROOT/'decks'/f'{n}.dck')==h
original=json.loads((WORK/'oct7-prefix-recovery/pending-records-structural.json').read_text())
jobs=[(r['variant'],r['seed'],r['seat_rotation']) for r in original]+[('Pure_GGS',202610060,r) for r in range(4)]
out=WORK/'amplifier-slots/archive-recovery-replays';out.mkdir(exist_ok=False);(out/'analysis').mkdir()
(out/'metadata.json').write_text(json.dumps({'protocol':P,'jobs':jobs,'workers':2,'timeout':600,'purpose':'actual unprofiled evidence recovery, not additional independent observations'},indent=2)+'\n')
def work(job):
 arm,seed,rotation=job
 rows=dragonmind.batch(WORK/'restored-v28/engine',jar,out,arm,rotation,[seed],600,True,True,extra_jvm_flags=('-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.casualSeven=true'))
 for row in rows:
  if row['status']!='completed':continue
  m,t=metrics.extract(out,row);m['variant']=arm;key=f'{arm}-{seed}-r{rotation}'
  (out/'analysis'/(key+'-metrics.json')).write_text(json.dumps(m,indent=2)+'\n')
  with gzip.open(out/'analysis'/(key+'-timeline.json.gz'),'wt',compresslevel=5) as f:json.dump(t,f,separators=(',',':'))
  for raw in (out/'audit'/Path(row['log']).stem).glob('*.jsonl'):
   gz=raw.with_suffix('.jsonl.gz');tmp=gz.with_suffix('.gz.tmp')
   with raw.open('rb') as src,gzip.open(tmp,'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
   with gzip.open(tmp,'rb') as check:
    while check.read(1<<20):pass
   tmp.replace(gz);raw.unlink()
  if m['measurement_gaps'] or m['snapshot_life_match_rate']!=1.0:row['status']='measurement_error'
 return rows
rows=[]
for rs in dragonmind.run_jobs(jobs,work,2,True):
 rows+=rs;tmp=out/'summary.tmp';tmp.write_text(json.dumps(rows,indent=2)+'\n');tmp.replace(out/'summary.json')
 print(json.dumps({'completed':len(rows),'requested':len(jobs),'last':[(r['variant'],r['seed'],r['seat_rotation'],r['status']) for r in rs]}),flush=True)
assert len(rows)==len(jobs) and all(r['status']=='completed' for r in rows),'Stop: recovery replay failure requires investigation'
