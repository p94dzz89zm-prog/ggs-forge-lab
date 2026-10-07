"""Adopt every preplanned variant identity from a fully passed clock gate once."""
from pathlib import Path
import json,shutil,sys
repo=Path(__file__).resolve().parents[2];w=repo.parent;sys.path.insert(0,str(repo/'experiments/amplifier-slots'));from checkpoint import save
out=w/'amplifier-slots';gate=json.loads((out/'decision-clock-gate-receipt.json').read_text());assert gate['passed'] and gate['games']==16
build=json.loads((w/'decision-clock-probe/build.json').read_text());amendment={'reason':'Five-second AI decision timeout; console/engine result disagreement correctly rejected in Throne and Karlach identities; Karlach reproduced in isolated actual Forge game','decision_seconds_before':5,'decision_seconds_after':30,'whole_game_seconds_unchanged':600,'workers_unchanged':2,'base_engine_sha256':build['base_sha256'],'runtime_engine_sha256':build['patched_sha256'],'runtime_jar':'decision-clock-probe/engine-decision-clock.jar','build':build,'gate':gate,'frozen_decks_unchanged':True,'rules_and_pilot_heuristics_unchanged':True,'fresh_import_validation':'final-import-validation.log'}
(out/'Pure_GGS_Decision_Clock_Amendment.json').write_text(json.dumps(amendment,indent=2)+'\n')
stage=out/'stage-128';source=out/'decision-clock-gate';rows=json.loads((stage/'summary.json').read_text());bad=[r for r in rows if r['status']!='completed'];assert len(rows)==39 and len(bad)==2
assert {(r['variant'],r['seed'],r['seat_rotation']) for r in bad}=={('Pure_Slot_Throne',202610088,0),('Pure_Slot_Karlach',202610088,0)}
ledger=json.loads((stage/'failed-attempts.json').read_text());keys=json.loads((stage/'saved-game-keys.json').read_text());existing={(r['variant'],r['seed'],r['seat_rotation']):r for r in rows};new_identities=[];recovered=[]
for r in json.loads((source/'summary.json').read_text()):
 identity=(r['variant'],r['seed'],r['seat_rotation']);old=existing.get(identity)
 if r['variant']=='Pure_GGS' or (old and old['status']=='completed'):continue
 assert r['status']=='completed' and r['seed']==202610088
 label=Path(r['log']).stem;key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";new={**r,'runtime_engine_sha256':build['patched_sha256'],'ai_decision_seconds':30,'adopted_from_reliability_gate':True}
 if old:
  historical=stage/'failed-attempts'/key;historical.mkdir(parents=True)
  for name in [old['log'],'engine-records/'+label,'audit/'+label]:
   p=stage/name
   if p.exists():dst=historical/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dst))
  original_console=(historical/old['log']).read_text();timeout_count=original_console.count('java.util.concurrent.TimeoutException');assert timeout_count>0
  new.update({'supersedes_failed_attempt':old,'recovery_proof':'decision-clock-recovery-proof.json','recovery_gate':'decision-clock-gate-receipt.json'})
  ledger.append({'original_record':old,'excluded_kind':'AI_decision_timeout','simulator_failure':True,'resolved':True,'replay_record':new,'evidence_directory':str(historical.relative_to(w))})
  recovered.append({'excluded_original':old,'original_console_decision_timeouts':timeout_count,'repaired_game':new});keys.remove(key)
 for name in [r['log'],'engine-records/'+label,'audit/'+label]:
  src=source/name;dst=stage/name;assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
  if src.is_dir():shutil.copytree(src,dst)
  else:shutil.copy2(src,dst)
 for src in (source/'analysis').glob(key+'-*'):
  dst=stage/'analysis'/src.name
  if src.name.endswith('-metrics.json'):
   m=json.loads(src.read_text());m['log']=str(m['log']).replace(str(source),str(stage));m['runtime_engine_sha256']=build['patched_sha256'];m['ai_decision_seconds']=30;dst.write_text(json.dumps(m,indent=2)+'\n')
  else:shutil.copy2(src,dst)
 if old:rows[rows.index(old)]=new
 else:rows.append(new);new_identities.append(identity)
assert len(recovered)==2 and len(new_identities)==9 and len(rows)==48 and all(r['status']=='completed' for r in rows)
proof={'recoveries':recovered,'isolated_Karlach_reproduction_decision_timeouts':3,'isolated_reproduction_status':'process_error','decision_seconds_after':30,'fresh_gate_passed':True,'canonical_old_bad_trajectory_equality_not_assumed':True,'each_identity_counted_once':True}
(out/'decision-clock-recovery-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
(stage/'adoption-receipt.json').write_text(json.dumps({'gate_passed':True,'existing_failed_identities_replaced_once':2,'preplanned_uncollected_identities_retained_once':new_identities,'prior_valid_games_not_overwritten':37,'no_outcome_selection':True},indent=2)+'\n')
(stage/'failed-attempts.json').write_text(json.dumps(ledger,indent=2)+'\n');(stage/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');(stage/'saved-game-keys.json').write_text(json.dumps(keys)+'\n');(stage/'performance.json').write_text(json.dumps({'valid':48,'requested':96,'attempted':48+len(ledger),'historical_excluded':len(ledger)})+'\n')
save(stage);print('Adopted two clean replacements and nine preplanned gate identities once; originals retained/excluded;592 valid cumulative')
