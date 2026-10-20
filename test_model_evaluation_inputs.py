import json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from evaluation_batch import policy_inputs,freeze_policy_inputs,policy_flags,verify_policy_inputs,resource_fingerprint
class ModelEvaluationInputs(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.file=self.root/'candidate.json';self.file.write_text(json.dumps({'format':1,'scope':'four_player_visible_survival_v1','features':['bias','public_lethal_exposure_delta'],'weights':[0,4.46]}));self.a=SimpleNamespace(candidate_model=self.file);self.out=self.root/'out';self.out.mkdir()
 def test_same_executable_pair_can_isolate_model_with_portable_snapshot(self):
  spec=policy_inputs(self.a);freeze_policy_inputs(self.a,self.out,spec);self.assertEqual(policy_flags(self.out,spec,'baseline'),[]);flags=policy_flags(self.out,spec,'candidate');self.assertEqual(len(flags),2);self.assertTrue(flags[0].endswith('/inputs/candidate-model.json'));self.assertTrue(flags[1].endswith(spec['candidate']['sha256']));verify_policy_inputs(self.a,self.out,spec)
 def test_changed_original_or_snapshot_never_reused(self):
  spec=policy_inputs(self.a);freeze_policy_inputs(self.a,self.out,spec);self.file.write_text('{}')
  with self.assertRaises(ValueError):verify_policy_inputs(self.a,self.out,spec)
  path=self.out/spec['candidate']['snapshot'];path.write_text('{}')
  with self.assertRaises(ValueError):policy_flags(self.out,spec,'candidate')
  with self.assertRaises(ValueError):freeze_policy_inputs(self.a,self.out,spec)
 def test_wrong_scope_and_nonfinite_weights_rejected(self):
  model=json.loads(self.file.read_text())
  for key,value in [('scope','scoped_counterspell_preference_v1'),('weights',[0,float('nan')]),('weights',[0]),('weights',[0,True])]:
   changed={**model,key:value};self.file.write_text(json.dumps(changed))
   with self.assertRaises(ValueError):policy_inputs(self.a)
 def test_frozen_identity_does_not_depend_on_restore_directory(self):
  spec=policy_inputs(self.a);freeze_policy_inputs(self.a,self.out,spec);other=self.root/'restored';other.mkdir();freeze_policy_inputs(self.a,other,spec);self.assertEqual((self.out/spec['candidate']['snapshot']).read_bytes(),(other/spec['candidate']['snapshot']).read_bytes());self.assertNotEqual(policy_flags(self.out,spec,'candidate')[0],policy_flags(other,spec,'candidate')[0]);self.assertEqual(policy_flags(self.out,spec,'candidate')[1],policy_flags(other,spec,'candidate')[1])
 def test_changed_card_definition_or_resource_inventory_changes_identity(self):
  res=self.root/'res';res.mkdir();card=res/'card.txt';card.write_text('first rules');before=resource_fingerprint(self.root);card.write_text('changed rules');self.assertNotEqual(before,resource_fingerprint(self.root));card.write_text('first rules');self.assertEqual(before,resource_fingerprint(self.root));(res/'new-card.txt').write_text('new rules');self.assertNotEqual(before,resource_fingerprint(self.root))
 def test_empty_or_symlinked_resources_not_frozen(self):
  with self.assertRaises(ValueError):resource_fingerprint(self.root)
  res=self.root/'res';res.mkdir()
  with self.assertRaises(ValueError):resource_fingerprint(self.root)
  (res/'link').symlink_to(self.file)
  with self.assertRaises(ValueError):resource_fingerprint(self.root)
