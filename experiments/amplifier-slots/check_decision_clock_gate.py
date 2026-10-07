import pathlib,sys,json,hashlib,gzip,shutil,time,importlib.util,subprocess
repo=pathlib.Path(__file__).resolve().parents[2];w=repo.parent;here=repo/'experiments/amplifier-slots';sys.path[:0]=[str(repo),str(here)];import dragonmind
from checkpoint import save
spec=importlib.util.spec_from_file_location('metrics',repo/'experiments/pure-ggs/analyze.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
from inspect_games import inspect
P=json.loads((here/'protocol.json').read_text());build=json.loads((w/'decision-clock-probe/build.json').read_text());jar=w/'decision-clock-probe/engine-decision-clock.jar';assert hashlib.sha256(jar.read_bytes()).hexdigest()==build['patched_sha256'];out=w/'amplifier-slots/decision-clock-gate';out.mkdir(exist_ok=True);(out/'analysis').mkdir(exist_ok=True)
arms=['Pure_GGS','Pure_Slot_Purphoros','Pure_Slot_Throne','Pure_Slot_Karlach'];jobs=[(v,202610060 if v=='Pure_GGS' else 202610088,r) for v in arms for r in range(4)]
metadata={'protocol':P,'seed':202610060,'seeds':1,'arms':arms,'gate':True,'workers':2,'timeout':600,'engine_resources':'restored-v28/engine','ai_decision_seconds':30,'runtime_engine_sha256':build['patched_sha256'],'seeds_by_variant':{v:202610060 if v=='Pure_GGS' else 202610088 for v in arms},'purpose':'Clock-only repair gate; four baseline seats and12 heavy-state variant seed/seat games'};(out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
def work(job):
 v,seed,r=job;rows=dragonmind.batch(w/'restored-v28/engine',jar,out,v,r,[seed],600,True,True,extra_jvm_flags=('-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.casualSeven=true','-Ddragonmind.aiDecisionTimeoutSeconds=30'))
 for row in rows:
  if row['status']!='completed':continue
  m,t=metrics.extract(out,row);m['variant']=v;key=f'{v}-{seed}-r{r}';(out/'analysis'/(key+'-metrics.json')).write_text(json.dumps(m,indent=2)+'\n')
  with gzip.open(out/'analysis'/(key+'-timeline.json.gz'),'wt') as f:json.dump(t,f)
  for a in (out/'audit'/pathlib.Path(row['log']).stem).glob('*.jsonl'):
   with a.open('rb') as f:
    for line in f:json.loads(line)
   with a.open('rb') as src,gzip.open(a.with_suffix('.jsonl.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
   with gzip.open(a.with_suffix('.jsonl.gz')) as f:
    while f.read(1<<20):pass
   a.unlink()
  if m['measurement_gaps'] or m['snapshot_life_match_rate']!=1:row['status']='measurement_error'
 return rows
rows=[]
for rs in dragonmind.run_jobs(jobs,work,2,True):
 rows+=rs;tmp=out/'summary.tmp';tmp.write_text(json.dumps(rows,indent=2)+'\n');tmp.replace(out/'summary.json');print({'finished':len(rows),'target':16,'last':[(r['variant'],r['seat_rotation'],r['status']) for r in rs]},flush=True);save(out)
assert len(rows)==16 and all(r['status']=='completed' for r in rows)
subprocess.run([sys.executable,str(here/'audit_integrity.py'),str(out),'--repair','--prune-raw'],check=True)
clean=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith(('DragonMind Result:','Game Outcome: Match Duration')))
checks=[]
for r in rows:
 i=inspect(out,r,["Night's Whisper"]);assert i['clamp_cleared'];c={'variant':r['variant'],'seed':r['seed'],'rotation':r['seat_rotation'],'status':'completed','clamp_cleared':True}
 if r['variant']=='Pure_GGS':
  old=w/f"pure-ggs/gate/engine-records/Pure_GGS__seat{r['seat_rotation']}__seeds202610060-202610060/202610060.log";c['canonical_baseline_byte_exact_except_elapsed']=clean((out/r['engine_transcript']).read_text())==clean(old.read_text());assert c['canonical_baseline_byte_exact_except_elapsed']
 checks.append(c)
receipt={'passed':True,'games':16,'workers':2,'batch_seconds':600,'decision_seconds':30,'build':build,'checks':checks};(w/'amplifier-slots/decision-clock-gate-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS16/16 clock-only reliability gate',flush=True)
