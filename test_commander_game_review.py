import json,tempfile,unittest
from pathlib import Path
from commander_game_review import audit_visibility,trajectory_digest
class CommanderEvidencePreflightTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.p=Path(t.name)/'seat-0.jsonl'
  self.row={'state':{'viewer_id':0,'viewer':'Ai(1)-GGS','turn':1,'phase':'MAIN1','active_player_id':1,'players':[{'id':0,'name':'Ai(1)-GGS','life':40,'hand':[]},{'id':1,'name':'Ai(2)-other','life':40,'hand_count':7,'library_count':92}],'stack':[]}}
 def write(self,rows):self.p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
 def test_clean_view_is_not_full_game_approval(self):
  self.write([self.row]);r=audit_visibility([self.p]);self.assertEqual(r['visibility_or_record_errors'],[]);self.assertEqual(r['snapshots_checked'],1);self.assertIsNone(r['model_activation_count'])
 def test_opponent_hand_or_library_leak_rejected(self):
  for key,value in [('hand',[{'name':'secret'}]),('library',[{'name':'secret'}])]:
   other=self.row['state']['players'][1];other[key]=value;self.write([self.row]);self.assertTrue(audit_visibility([self.p])['visibility_or_record_errors']);del other[key]
 def test_missing_or_backwards_view_cannot_pass(self):
  self.assertTrue(audit_visibility([])['visibility_or_record_errors']);other=json.loads(json.dumps(self.row));other['state']['turn']=0;self.write([self.row,other]);self.assertTrue(audit_visibility([self.p])['visibility_or_record_errors'])
 def test_only_final_metadata_ignored_in_trajectory_comparison(self):
  a=self.p.parent/'a.log';b=self.p.parent/'b.log';a.write_text('A attacks B\nDragonMind Result: {"engine_ms":1}\n');b.write_text('A attacks B\nDragonMind Result: {"engine_ms":2}\n');self.assertEqual(trajectory_digest(a),trajectory_digest(b));b.write_text('B attacks A\nDragonMind Result: {"engine_ms":2}\n');self.assertNotEqual(trajectory_digest(a),trajectory_digest(b))
