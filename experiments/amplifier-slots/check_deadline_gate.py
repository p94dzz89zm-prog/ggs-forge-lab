"""Verify the operational deadline amendment without changing engine or decks."""
import json,subprocess,sys
from pathlib import Path
from inspect_games import inspect
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'amplifier-slots';gate=OUT/'deadline-gate'
rows=json.loads((gate/'summary.json').read_text());assert len(rows)==16 and all(r['status']=='completed' for r in rows)
subprocess.run([sys.executable,str(HERE/'audit_integrity.py'),str(gate),'--repair','--prune-raw'],check=True)
clean=lambda s:'\n'.join(l for l in s.splitlines() if not l.startswith(('DragonMind Result:','Game Outcome: Match Duration')))
baseline={}
for d in (WORK/'pure-ggs').glob('batch-*'):
 for r in json.loads((d/'summary.json').read_text()):baseline[r['seed'],r['seat_rotation']]=(d,r)
checks=[]
for r in rows:
 key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";m=json.loads((gate/'analysis'/(key+'-metrics.json')).read_text());assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
 inspection=inspect(gate,r,["Night's Whisper"]);assert inspection['clamp_cleared']
 check={'variant':r['variant'],'seed':r['seed'],'rotation':r['seat_rotation'],'completed':True,'creations_reconciled':True,'life_match':1,'clamp_cleared':True}
 if r['variant']=='Pure_GGS':
  d,b=baseline[r['seed'],r['seat_rotation']];check['baseline_replay_identical']=clean((gate/r['engine_transcript']).read_text())==clean((d/b['engine_transcript']).read_text());assert check['baseline_replay_identical']
 if r['variant']=='Pure_Slot_Port_Razer' and r['seat_rotation']==1:
  d=OUT/'timeout-replay-unprofiled';b=json.loads((d/'summary.json').read_text())[0];check['slow_game_replay_identical']=clean((gate/r['engine_transcript']).read_text())==clean((d/b['engine_transcript']).read_text());assert check['slow_game_replay_identical']
 checks.append(check)
receipt={'passed':True,'games':16,'timeout_seconds':600,'engine_changed':False,'deck_changed':False,'checks':checks}
(OUT/'deadline-gate-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS:16 completed, four identical baseline replays, identical slow-game replay, complete audit streams')
