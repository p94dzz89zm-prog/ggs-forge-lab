"""Synthetic admission contracts; no empirical strategic claims."""
import json,tempfile,unittest
from pathlib import Path
import multiplayer_preference as m
from tactical_preference import probability
class MultiplayerPreferenceTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.p=Path(t.name);self.rows=[]
  for i,protect in enumerate([False,True]):
   def outcome(counter):
    attacks=counter!=protect;life=4-10*int(attacks)
    return {'countered':counter,'survives':life>0,'life':life,'targetSurvives':counter,'swanRetained':not counter,'blueUntapped':not counter,'birds':int(counter),'attackLegal':attacks}
   self.rows.append({'id':str(i),'purpose':'development','scope':m.SCOPE,'legal_paid_resolved':True,'body':'synthetic','life':4,'features':[1,1 if protect else -1],'counter_outcome':outcome(True),'pass_outcome':outcome(False)})
  self.review={'scope':m.SCOPE,'purpose':'development','reviewer':'unit test','findings':['Synthetic fixture, not gameplay'],'unresolved_in_scope':[],'full_game_admission':False,'completion_marker':'Checks passed: 4','accepted_ids':['0','1'],'labels':{'0':0,'1':1},'independent_body_power':{'synthetic':10}};self.save()
 def save(self):
  (self.p/'decisions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in self.rows));(self.p/'engine.log').write_text(''.join('MULTIPLAYER_DATA '+json.dumps(r)+'\n' for r in self.rows)+'Checks passed: 4\n');self.review.update(data_sha256=m.sha(self.p/'decisions.jsonl'),engine_log_sha256=m.sha(self.p/'engine.log'));(self.p/'review.json').write_text(json.dumps(self.review))
 def test_fit_reload_and_immutable_checkpoint(self):
  out=self.p/'model';model=m.train(self.p,out);self.assertEqual(model,json.loads(out.read_text()));self.assertLess(probability(model['weights'],[1,-1]),.25);self.assertGreater(probability(model['weights'],[1,1]),.75);self.assertFalse(model['promotion']);self.assertEqual(model['full_game_admissions'],0)
  with self.assertRaises(FileExistsError):m.train(self.p,out)
 def test_heldout_even_with_consistent_review_cannot_train(self):
  for r in self.rows:r['purpose']='heldout_evaluation'
  self.save()
  with self.assertRaises(ValueError):m.train(self.p,self.p/'model')
 def test_rehashed_wrong_actual_damage_is_rejected(self):
  self.rows[0]['counter_outcome']['life']=-5;self.save()
  with self.assertRaises(ValueError):m.load_reviewed(self.p)
 def test_feature_and_label_spoofing_rejected(self):
  self.rows[0]['features']=[1,1];self.save()
  with self.assertRaises(ValueError):m.load_reviewed(self.p)
  self.rows[0]['features']=[1,-1];self.review['labels']['0']=1;self.save()
  with self.assertRaises(ValueError):m.load_reviewed(self.p)
 def test_no_survival_contrast_abstains(self):
  row=json.loads(json.dumps(self.rows[0]));row['pass_outcome']=dict(row['counter_outcome']);row['pass_outcome'].update(countered=False,targetSurvives=False,swanRetained=True,blueUntapped=True,birds=0)
  with self.assertRaises(ValueError):m.audit_pair(row,10)
 def test_missing_review_and_changed_log_rejected(self):
  self.review['reviewer']='';self.save()
  with self.assertRaises(ValueError):m.load_reviewed(self.p)
  self.review['reviewer']='test';self.save();(self.p/'engine.log').write_text('Checks passed: 4\n')
  with self.assertRaises(ValueError):m.load_reviewed(self.p)
