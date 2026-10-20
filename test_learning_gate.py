"""Synthetic admission fixtures, not empirical Magic gameplay evidence."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from learning_gate import assess, fingerprint, feedback, FULL_SCOPE, MECHANICS
from policy_search import BASE, parent_candidate, review_game
from referee_games import inspect


class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  (self.root/"res/ai").mkdir(parents=True);(self.root/"res/ai/Default.ai").write_text("PLAY_AGGRO=false\n")
  self.record={'seed':77,'status':'completed','winner':'Ai(1)-GGS_Current','engine_ms':12}
  self.game={**self.record,'variant':'GGS_Current','seats':['GGS_Current','Jaymie_Ezio','Gabe_Food','Destyn_Turtles'],'engine_record':'engine-records/game/77.json','engine_transcript':'engine-records/game/77.log','log':'game.log'}
  for name in ['engine-records/game','audit/game']:(self.root/name).mkdir(parents=True)
  (self.root/self.game['engine_record']).write_text(json.dumps(self.record))
  text='DragonMind Result: '+json.dumps(self.record)+'\n'
  (self.root/self.game['engine_transcript']).write_text(text);(self.root/'game.log').write_text(text)
  for i,name in enumerate(self.game['seats']):
   (self.root/f'audit/game/seat-{i}.jsonl').write_text(json.dumps({'kind':'priority','state':{'viewer':f'Ai({i+1})-{name}','viewer_id':i,'active_player_id':i,'turn':1,'phase':'MAIN1','players':[{'id':i,'hand':[],'hand_count':0,'life':40,'battlefield':[]}]},'decision':{'action':'pass'}})+'\n')
  self.signature={'purpose':'development','jar_sha256':'a'*64,'deck_sha256':{s:'b'*64 for s in self.game['seats']}}
  self.reports=inspect(self.root)
 def review(self):
  return {'version':1,'scope':FULL_SCOPE,'evidence_fingerprint':fingerprint(self.root,self.game,self.signature,BASE),'rules_status':'pass','critical_decisions_status':'pass','reviewed_seats':self.game['seats'],'reviewed_mechanics':sorted(MECHANICS),'unresolved_issues':[],'limitations':[],'reviewer':'synthetic test','findings':['Admission fixture only, not a reviewed real Magic game.']}
 def gate(self,review=None):return assess(self.root,self.game,self.reports,self.signature,BASE,review)
 def test_integrity_only_result_cannot_train(self):
  self.assertTrue(self.reports[0]['record_integrity_passed']);self.assertEqual(self.gate()['status'],'pending_review')
 def test_full_bound_review_can_admit_synthetic_fixture(self):
  self.assertEqual(self.gate(self.review())['status'],'approved_for_learning')
 def test_partial_scope_cannot_admit_global_outcome(self):
  r=self.review();r['scope']='one mana payment';self.assertEqual(self.gate(r)['status'],'quarantined')
 def test_rules_only_strategy_only_or_material_mistake_cannot_train(self):
  for change in [{'rules_status':'pending'},{'critical_decisions_status':'pending'},{'unresolved_issues':['Missed payable defense']}]:
   r=self.review();r.update(change);self.assertNotEqual(self.gate(r)['status'],'approved_for_learning')
 def test_unknowns_or_missing_explicit_clearance_block_admission(self):
  for change in [{'limitations':['Timing unknown']},{'unresolved_issues':None},{'limitations':None}]:
   r=self.review();r.update(change);self.assertNotEqual(self.gate(r)['status'],'approved_for_learning')
 def test_all_seats_and_mechanics_required(self):
  for change in [{'reviewed_seats':self.game['seats'][:1]},{'reviewed_mechanics':['combat_and_damage']}]:
   r=self.review();r.update(change);self.assertNotEqual(self.gate(r)['status'],'approved_for_learning')
 def test_heldout_never_trains_even_if_reviewed(self):
  r=self.review();self.signature['purpose']='heldout';self.assertEqual(self.gate(r)['status'],'evaluation_only')
 def test_approval_invalidates_after_evidence_changes(self):
  for name in ['game.log',self.game['engine_transcript'],'audit/game/seat-0.jsonl']:
   r=self.review();p=self.root/name;original=p.read_text();p.write_text(original+'\n');self.assertEqual(self.gate(r)['status'],'quarantined');p.write_text(original)
 def test_bound_to_build_deck_and_weights(self):
  for key in ['jar_sha256','deck_sha256']:
   r=self.review();original=copy.deepcopy(self.signature[key]);self.signature[key]='changed';self.assertEqual(self.gate(r)['status'],'quarantined');self.signature[key]=original
  r=self.review();self.assertEqual(assess(self.root,self.game,self.reports,self.signature,{**BASE,'dragon':0},r)['status'],'quarantined')
 def test_incomplete_corrupt_or_failed_games_quarantined(self):
  for status in ['timeout','engine_error','running']:
   self.game['status']=status;self.assertEqual(self.gate(self.review())['status'],'quarantined')
  self.game['status']='completed';self.reports[0]['record_integrity_passed']=False;self.assertEqual(self.gate(self.review())['status'],'quarantined')
 def test_missing_audit_or_escaped_path_cannot_be_approved(self):
  r=self.review();(self.root/'audit/game/seat-0.jsonl').unlink();self.assertEqual(self.gate(r)['status'],'quarantined');self.game['log']='../outside.log';self.assertEqual(self.gate(r)['status'],'quarantined')
 def test_malformed_review_fails_closed(self):
  for value in [[],42,{'reviewed_seats':None}]:self.assertNotEqual(self.gate(value)['status'],'approved_for_learning')
  for field in ['reviewed_seats','reviewed_mechanics','reviewer']:
   r=self.review();r[field]=None;self.assertNotEqual(self.gate(r)['status'],'approved_for_learning')
 def test_legacy_numeric_feedback_never_selects_parent(self):
  self.assertIsNone(parent_candidate([{'games':[{'feedback':1,'won':True}]}],random.Random(1)))
 def test_reviewed_losses_usable_but_stale_fingerprint_not_usable(self):
  row={'feedback':0.0,'learning_gate':self.gate(self.review())};self.assertEqual(feedback(row),0.0);self.assertEqual(parent_candidate([{'games':[row]}],random.Random(1)),0)
  row['learning_gate']['reviewed_fingerprint']='stale';self.assertIsNone(feedback(row))
 def test_pipeline_retains_result_without_learning_from_it(self):
  row=review_game(self.root,self.game,self.signature,BASE);self.assertEqual(row['observed_outcome'],1.0);self.assertIsNone(row['feedback']);self.assertIsNone(parent_candidate([{'games':[row]}],random.Random(1)))
 def test_pipeline_rechecks_approved_evidence(self):
  (self.root/'learning-review.json').write_text(json.dumps(self.review()));row=review_game(self.root,self.game,self.signature,BASE);self.assertEqual(row['feedback'],1.0)
  (self.root/'audit/game/seat-0.jsonl').write_text('changed');review_game(self.root,row,self.signature,BASE);self.assertIsNone(row['feedback'])
 def test_saved_result_disagreement_quarantined(self):
  self.game['winner']='Ai(2)-Jaymie_Ezio';self.assertEqual(self.gate(self.review())['status'],'quarantined')
 def test_missing_engine_or_deck_provenance_cannot_be_admitted(self):
  for key in ['jar_sha256','deck_sha256']:
   original=self.signature.pop(key);self.assertEqual(self.gate(self.review())['status'],'quarantined');self.signature[key]=original
 def test_selected_seat_audit_cannot_justify_all_seat_approval(self):
  for i in [1,2,3]:(self.root/f'audit/game/seat-{i}.jsonl').unlink()
  self.assertNotEqual(self.gate(self.review())['status'],'approved_for_learning')
 def test_collector_supports_all_seats_without_sharing_pilot_information(self):
  from unittest.mock import patch
  from types import SimpleNamespace
  import dragonmind
  for all_seats in [False,True]:
   out=self.root/('all' if all_seats else 'selected');out.mkdir()
   with patch('dragonmind.subprocess.run',return_value=SimpleNamespace(returncode=0)) as launch:
    dragonmind.batch(self.root,self.root/'synthetic.jar',out,'GGS_Current',0,[77],1,True,True,audit_all_seats=all_seats)
   command=launch.call_args.args[0];self.assertEqual(any(x.startswith('-Dforge.audit.player=') for x in command),not all_seats)
   self.assertTrue(any(x.startswith('-Dforge.ai.ggsPilotPlayer=') for x in command))
 def test_all_seat_audits_do_not_mix_opponents_into_weakness_tracking(self):
  from research_tools import watch
  # The collector's label starts with the deck variant in actual games.
  audit=self.root/'audit/game';audit.rename(self.root/'audit/GGS_Current__seat0')
  record=self.root/'engine-records/game';record.rename(self.root/'engine-records/GGS_Current__seat0')
  result=watch([self.root],self.root/'watch-output')
  self.assertEqual(result['integrity_passed_games_with_selected_seat_audits'],1)
  self.assertEqual(result['trusted_card_recommendation_games'],0)


class ProfileAdmissionTests(unittest.TestCase):
 def test_narrow_review_recorded_but_not_global_learning(self):
  from test_adaptive_pilot import EvidenceFaultTests
  import adaptive_pilot as a
  from review_experience import record_review
  with tempfile.TemporaryDirectory() as td:
   db,root,attempt,e=EvidenceFaultTests().fixture(td);record_review(db,str(root),0,'pass','one payment','Synthetic scoped finding','test');self.assertEqual(a.statistics(db,'fixture',True)['BALANCED']['n'],0);db.close()
 def test_profile_review_bound_to_current_evidence(self):
  from test_adaptive_pilot import EvidenceFaultTests
  import adaptive_pilot as a
  from review_experience import record_review
  with tempfile.TemporaryDirectory() as td:
   db,root,attempt,e=EvidenceFaultTests().fixture(td);signature={'purpose':'development','jar_sha256':'a'*64,'deck_sha256':{s:'b'*64 for s in e['game']['seats']}};(root/'manifest.json').write_text(json.dumps(signature));audit=attempt/'audit/seat-0.jsonl';audit.parent.mkdir()
   for i,name in enumerate(e['game']['seats']):(attempt/f'audit/seat-{i}.jsonl').write_text(json.dumps({'state':{'viewer':f'Ai({i+1})-{name}','viewer_id':i,'players':[{'id':i,'hand':[]}]}})+'\n')
   review={'version':1,'scope':FULL_SCOPE,'evidence_fingerprint':fingerprint(attempt,e['game'],signature,{'profile':'BALANCED'}),'rules_status':'pass','critical_decisions_status':'pass','reviewed_seats':e['game']['seats'],'reviewed_mechanics':sorted(MECHANICS),'unresolved_issues':[],'limitations':[],'reviewer':'test','findings':['Synthetic review only']}
   (attempt/'learning-review.json').write_text(json.dumps(review));record_review(db,str(root),0,'pass',FULL_SCOPE,'Synthetic bound admission','test');self.assertEqual(a.statistics(db,'fixture',True)['BALANCED']['n'],1)
   audit.write_text('changed');self.assertEqual(a.statistics(db,'fixture',True)['BALANCED']['n'],0);db.close()


if __name__=='__main__':unittest.main()
