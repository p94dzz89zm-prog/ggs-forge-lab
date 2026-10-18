"""Fail closed when parseable streams drift after finalization."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from commander_game_review import saved_evidence,trajectory_digest
class SavedGameEvidenceTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.parent=Path(t.name);self.root=self.parent/'candidate';self.root.mkdir();self.stream=self.root/'audit.jsonl';self.stream.write_text('{"turn":1}\n{"turn":2}\n')
  self.entry={'label':'candidate','status':'saved','complete':True,'evidence_sha256':{'audit.jsonl':hashlib.sha256(self.stream.read_bytes()).hexdigest()}}
  self.write_state()
 def write_state(self):(self.parent/'state.json').write_text(json.dumps({'attempts':[self.entry]}))
 def test_original_passes_but_parseable_tail_loss_rejected(self):
  self.assertTrue(saved_evidence(self.root)['passed']);self.stream.write_text('{"turn":1}\n');r=saved_evidence(self.root);self.assertFalse(r['passed']);self.assertIn('hash mismatch',r['issues'][0]['issue'])
 def test_missing_extra_and_unknown_evidence_rejected(self):
  self.stream.unlink();self.assertFalse(saved_evidence(self.root)['passed']);self.stream.write_text('{}\n');self.entry['status']='running';self.write_state();self.assertFalse(saved_evidence(self.root)['passed'])
  self.entry['status']='saved';self.entry['evidence_sha256']['audit.jsonl']=hashlib.sha256(self.stream.read_bytes()).hexdigest();self.write_state();(self.root/'unbound.log').write_text('extra');self.assertFalse(saved_evidence(self.root)['passed'])
 def test_unjournaled_and_unsafe_paths_rejected(self):
  (self.parent/'state.json').unlink();self.assertFalse(saved_evidence(self.root)['passed']);self.entry['evidence_sha256']={'../outside.log':'0'*64};self.write_state();self.assertFalse(saved_evidence(self.root)['passed'])
 def test_gameplay_equality_ignores_duration_but_not_damage(self):
  a=self.parent/'a';b=self.parent/'b';a.write_text('Damage: 3\nGame Outcome: Match Duration 0m : 33s\nDragonMind Result: {"engine_ms":1}\n');b.write_text('Damage: 3\nGame Outcome: Match Duration 0m : 31s\nDragonMind Result: {"engine_ms":2}\n');self.assertEqual(trajectory_digest(a),trajectory_digest(b));b.write_text('Damage: 4\n');self.assertNotEqual(trajectory_digest(a),trajectory_digest(b))
