"""Explicitly retain an excluded timeout and adopt its verified completed replay once."""
import gzip,importlib.util,json,shutil,sys
from pathlib import Path
from checkpoint import save
from inspect_games import inspect
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots';d=OUT/'stage-032';source=OUT/'timeout-replay-unprofiled'
gate=json.loads((OUT/'deadline-gate-receipt.json').read_text());proof=json.loads((source/'replay-check.json').read_text());assert gate['passed'] and gate['games']==16 and proof['identical_original_canonical_prefix']
rows=json.loads((d/'summary.json').read_text());b=json.loads((source/'summary.json').read_text())[0]
identity=lambda r:(r['variant'],r['seed'],r['seat_rotation']);old=next(r for r in rows if identity(r)==identity(b));assert old['status']=='timeout' and b['status']=='completed' and old['seats']==b['seats']
clean=lambda s:[l for l in s.splitlines() if not l.startswith(('DragonMind Result:','Game Outcome: Match Duration'))]
x=clean((d/old['engine_transcript']).read_text());y=clean((source/b['engine_transcript']).read_text());assert y[:len(x)]==x
# Compare the actual commands, allowing only paths and deadline to differ.
def normalize(cmd):
 result=[];skip=False
 for i,v in enumerate(cmd):
  if skip:skip=False;continue
  if v=='-c':result.extend([v,'DEADLINE']);skip=True
  elif v.startswith(('-Duser.home=','-Dforge.audit.directory=','-Ddragonmind.resultDirectory=')):result.append(v.split('=')[0]+'=OUTPUT')
  else:result.append(v)
 return result
assert normalize(old['command'])==normalize(b['command']) and not any('StartFlightRecording' in x for x in b['command'])
key=f"{b['variant']}-{b['seed']}-r{b['seat_rotation']}";label=Path(b['log']).stem;history=d/'failed-attempts'/key;history.mkdir(parents=True,exist_ok=False)
for p in [d/old['log'],d/'audit'/label,d/'engine-records'/label]:
 target=history/p.relative_to(d);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(target))
for p in [source/b['log'],source/'audit'/label,source/'engine-records'/label]:
 target=d/p.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
 if p.is_dir():shutil.copytree(p,target)
 else:shutil.copy2(p,target)
spec=importlib.util.spec_from_file_location('pure_metrics',ROOT/'experiments/pure-ggs/analyze.py');metrics=importlib.util.module_from_spec(spec);spec.loader.exec_module(metrics)
m,t=metrics.extract(d,b);m['variant']=b['variant'];assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
(d/'analysis'/(key+'-metrics.json')).write_text(json.dumps(m,indent=2)+'\n')
with gzip.open(d/'analysis'/(key+'-timeline.json.gz'),'wt',compresslevel=5) as f:json.dump(t,f,separators=(',',':'))
for p in (d/'audit'/label).glob('*.jsonl'):
 target=p.with_suffix('.jsonl.gz');tmp=target.with_suffix('.gz.tmp')
 with p.open('rb') as src,gzip.open(tmp,'wb',compresslevel=5) as dst:shutil.copyfileobj(src,dst)
 with gzip.open(tmp,'rb') as f:
  while f.read(1<<20):pass
 tmp.replace(target);p.unlink()
assert inspect(d,b,["Night's Whisper"])['clamp_cleared']
b['supersedes_failed_attempt']=old;b['recovery_proof']='timeout-replay-unprofiled/replay-check.json';b['recovery_gate']='deadline-gate-receipt.json'
ledger={'original_record':old,'excluded':True,'resolved':True,'resolution':'Exact unprofiled prefix replay completed under 600-second deadline; fresh 16-game gate passed.','preserved_directory':str(history.relative_to(WORK)),'completed_replay':identity(b),'proof':proof,'gate':gate}
(d/'failed-attempts.json').write_text(json.dumps([ledger],indent=2)+'\n')
(d/'run-amendments.json').write_text(json.dumps({'timeout_before':300,'timeout_after':600,'reason':proof['diagnosis'],'gate':gate,'retained_failed_attempts':1},indent=2)+'\n')
rows=[b if identity(r)==identity(b) else r for r in rows];(d/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
state=d/'saved-game-keys.json';done=json.loads(state.read_text());done.remove(key);state.write_text(json.dumps(done)+'\n')
(d/'adoption-receipt.json').write_text(json.dumps(ledger,indent=2)+'\n');save(d)
print('Adopted completed replay once; original timeout excluded and preserved. Remaining jobs may resume.')
