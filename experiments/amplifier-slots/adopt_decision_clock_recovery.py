from pathlib import Path
import json,hashlib,shutil,sys
repo=Path(__file__).resolve().parents[2];w=repo.parent;sys.path.insert(0,str(repo/'experiments/amplifier-slots'));from checkpoint import save
out=w/'amplifier-slots';gate=json.loads((out/'decision-clock-gate-receipt.json').read_text());assert gate['passed'] and gate['games']==16
build=json.loads((w/'decision-clock-probe/build.json').read_text());amendment={'reason':'Five-second AI decision timeout reproduced in an isolated actual Forge game; console/engine result disagreement correctly rejected','decision_seconds_before':5,'decision_seconds_after':30,'whole_game_seconds_unchanged':600,'workers_unchanged':2,'base_engine_sha256':build['base_sha256'],'runtime_engine_sha256':build['patched_sha256'],'runtime_jar':'decision-clock-probe/engine-decision-clock.jar','build':build,'gate':gate,'frozen_decks_unchanged':True,'rules_and_pilot_heuristics_unchanged':True,'fresh_import_validation':'final-import-validation.log'}
(out/'Pure_GGS_Decision_Clock_Amendment.json').write_text(json.dumps(amendment,indent=2)+'\n')
stage=out/'stage-128';source=out/'decision-clock-gate';rows=json.loads((stage/'summary.json').read_text());bad=[r for r in rows if r['status']!='completed'];assert len(bad)==1;old=bad[0];assert (old['variant'],old['seed'],old['seat_rotation'])==('Pure_Slot_Karlach',202610088,0)
new=next(r for r in json.loads((source/'summary.json').read_text()) if (r['variant'],r['seed'],r['seat_rotation'])==(old['variant'],old['seed'],old['seat_rotation']));assert new['status']=='completed'
label=Path(old['log']).stem;key=f"{old['variant']}-{old['seed']}-r{old['seat_rotation']}";historical=stage/'failed-attempts'/key;historical.mkdir(parents=True)
for name in [old['log'],'engine-records/'+label,'audit/'+label]:
 p=stage/name
 if p.exists():dst=historical/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dst))
for name in [new['log'],'engine-records/'+label,'audit/'+label]:
 p=source/name;dst=stage/name;dst.parent.mkdir(parents=True,exist_ok=True)
 if p.is_dir():shutil.copytree(p,dst)
 else:shutil.copy2(p,dst)
for p in (source/'analysis').glob(key+'-*'):
 dst=stage/'analysis'/p.name
 if p.name.endswith('-metrics.json'):
  m=json.loads(p.read_text());m['log']=str(m['log']).replace(str(source),str(stage));m['runtime_engine_sha256']=build['patched_sha256'];m['ai_decision_seconds']=30;dst.write_text(json.dumps(m,indent=2)+'\n')
 else:shutil.copy2(p,dst)
proof={'excluded_original':old,'original_console_decision_timeouts':4,'isolated_reproduction_decision_timeouts':3,'isolated_reproduction_status':'process_error','repaired_game':new,'decision_seconds_after':30,'fresh_gate_passed':True,'canonical_old_bad_trajectory_equality_not_assumed':True,'one_valid_experimental_identity_not_extra_gate_observation':True}
(out/'decision-clock-recovery-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
new={**new,'runtime_engine_sha256':build['patched_sha256'],'ai_decision_seconds':30,'supersedes_failed_attempt':old,'recovery_proof':'decision-clock-recovery-proof.json','recovery_gate':'decision-clock-gate-receipt.json','adopted_from_reliability_gate':True}
ledger=json.loads((stage/'failed-attempts.json').read_text());ledger.append({'original_record':old,'excluded_kind':'AI_decision_timeout','simulator_failure':True,'resolved':True,'replay_record':new,'evidence_directory':str(historical.relative_to(w))});(stage/'failed-attempts.json').write_text(json.dumps(ledger,indent=2)+'\n')
rows[rows.index(old)]=new;(stage/'summary.json').write_text(json.dumps(rows,indent=2)+'\n');keys=json.loads((stage/'saved-game-keys.json').read_text());keys.remove(key);(stage/'saved-game-keys.json').write_text(json.dumps(keys)+'\n')
(stage/'performance.json').write_text(json.dumps({'valid':39,'requested':96,'attempted':39+len(ledger),'historical_excluded':len(ledger)})+'\n')
save(stage);print('Adopted one clean clock-gate identity; original timeout retained/excluded; 583 valid cumulative')
