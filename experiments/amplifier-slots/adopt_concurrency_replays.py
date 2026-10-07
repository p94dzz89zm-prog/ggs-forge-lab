"""Preserve both excluded attempts and adopt gated completions exactly once."""
import gzip,importlib.util,json,shutil,sys
from pathlib import Path
from checkpoint import save
from inspect_games import inspect
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots';d=OUT/'stage-064';source=OUT/'concurrency-gate'
gate=json.loads((OUT/'concurrency-gate-receipt.json').read_text());assert gate['passed'] and gate['games']==16 and gate['workers_after']==2
rows=json.loads((d/'summary.json').read_text());source_rows=json.loads((source/'summary.json').read_text());identity=lambda r:(r['variant'],r['seed'],r['seat_rotation']);ledgers=[]
for proof in gate['original_timeout_prefix_proofs']:
 assert proof['verified']
 b=dict(next(r for r in source_rows if identity(r)==(proof['variant'],202610070,2)))
 old=next(r for r in rows if identity(r)==identity(b));assert old['status']=='timeout' and b['status']=='completed' and b['engine_ms']<600000
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
 b['supersedes_failed_attempt']=old;b['recovery_proof']='concurrency-gate-receipt.json';b['recovery_gate']='concurrency-gate-receipt.json'
 ledger={'original_record':old,'excluded':True,'resolved':True,'resolution':'Fresh two-worker 600-second gate completion retained; original canonical actions and all priority states/decisions preserved; additional nonplay hooks and one omitted candidate-evaluation invocation are explicitly documented.','preserved_directory':str(history.relative_to(WORK)),'completed_replay':identity(b),'proof':proof,'gate':'concurrency-gate-receipt.json'}
 ledgers.append(ledger);rows=[b if identity(r)==identity(b) else r for r in rows]
 state=d/'saved-game-keys.json';done=json.loads(state.read_text());done.remove(key);state.write_text(json.dumps(done)+'\n')
(d/'failed-attempts.json').write_text(json.dumps(ledgers,indent=2)+'\n')
(d/'run-amendments.json').write_text(json.dumps({'workers_before':4,'workers_after':2,'reason':gate['diagnosis'],'gate':gate,'retained_failed_attempts':2},indent=2)+'\n')
(d/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');(d/'adoption-receipt.json').write_text(json.dumps(ledgers,indent=2)+'\n')
(OUT/'Pure_GGS_Concurrency_Amendment.json').write_text(json.dumps({'workers_before':4,'workers_after':2,'timeout_before':600,'timeout_after':600,'engine_changed':False,'deck_changed':False,'gate':gate,'excluded_attempts':ledgers,'gate_recovery_games_reused_not_additional_independent_observations':2},indent=2)+'\n')
save(d);print('Adopted two gated completions once; original excluded attempts retained.')
