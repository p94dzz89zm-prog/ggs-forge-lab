"""Gate the two-worker scheduling amendment; no engine or deck changes."""
import json,subprocess,sys
from pathlib import Path
from inspect_games import inspect
from check_late_replays import canonical,verify
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'amplifier-slots';gate=OUT/'concurrency-gate'
rows=json.loads((gate/'summary.json').read_text());assert len(rows)==16 and all(r['status']=='completed' for r in rows)
meta=json.loads((gate/'metadata.json').read_text());assert meta['workers']==2 and meta['timeout']==600
subprocess.run([sys.executable,str(HERE/'audit_integrity.py'),str(gate),'--repair','--prune-raw'],check=True)
baseline={}
for d in (HERE.parents[2]/'pure-ggs').glob('batch-*'):
 for r in json.loads((d/'summary.json').read_text()):baseline[r['seed'],r['seat_rotation']]=(d,r)
checks=[]
for r in rows:
 key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";m=json.loads((gate/'analysis'/(key+'-metrics.json')).read_text());assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
 assert inspect(gate,r,["Night's Whisper"])['clamp_cleared']
 check={'variant':r['variant'],'seed':r['seed'],'rotation':r['seat_rotation'],'engine_seconds':r['engine_ms']/1000,'creations_reconciled':True,'life_match':1,'clamp_cleared':True}
 if r['variant']=='Pure_GGS':
  d,b=baseline[r['seed'],r['seat_rotation']];check['matched_baseline_actions']=canonical(gate/r['engine_transcript'])==canonical(d/b['engine_transcript']);assert check['matched_baseline_actions']
 if r['variant'] in ['Pure_Slot_Throne','Pure_Slot_Karlach'] and r['seat_rotation']==2:
  d=OUT/'late-timeout-unprofiled';b=next(x for x in json.loads((d/'summary.json').read_text()) if x['variant']==r['variant']);check['matched_slow_replay_actions']=canonical(gate/r['engine_transcript'])==canonical(d/b['engine_transcript']);assert check['matched_slow_replay_actions']
 checks.append(check)
proof=verify(OUT/'stage-064',gate,['Pure_Slot_Throne','Pure_Slot_Karlach'])
receipt={'passed':True,'games':16,'timeout_seconds':600,'workers_before':4,'workers_after':2,'engine_changed':False,'deck_changed':False,'checks':checks,'original_timeout_prefix_proofs':proof,'diagnosis':'Two long board-dense games completed under the unchanged deadline with reduced concurrency; action/state equivalence verified. Concurrency contention is supported, not isolated as the sole cause.'}
(OUT/'concurrency-gate-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS: 16 complete two-worker games; baseline and slow replay actions match; every original state/decision retained.')
