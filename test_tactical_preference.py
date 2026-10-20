"""Controlled learner contracts; these fixtures are not empirical game evidence."""
import json,tempfile,unittest
from pathlib import Path
import tactical_preference as t
class TacticalPreferenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.rows=[{'id':str(i),'purpose':'development','scope':t.SCOPE,'legal_paid_resolved':True,'features':[1,own,.3,.9],'counter_outcome':{'survives':True},'pass_outcome':{'survives':False}} for i,own in enumerate([-1,1])];self.save()
 def save(self):
  (self.root/'decisions.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in self.rows));(self.root/'engine.log').write_text(''.join('TACTICAL_DATA '+json.dumps(x)+'\n' for x in self.rows)+'Checks passed: 4\n')
  self.review={'scope':t.SCOPE,'purpose':'development','reviewer':'unit-test fixture','findings':['Numerical feedback fixture, not game evidence'],'unresolved_in_scope':[],'data_sha256':t.sha(self.root/'decisions.jsonl'),'engine_log_sha256':t.sha(self.root/'engine.log'),'completion_marker':'Checks passed: 4','accepted_ids':[x['id'] for x in self.rows],'labels':{'0':0,'1':1}};self.write_review()
 def write_review(self):(self.root/'review.json').write_text(json.dumps(self.review))
 def test_update_changes_predictions_and_survives_reload(self):
  out=self.root/'model.json';m=t.train(self.root,out);self.assertEqual(m,json.loads(out.read_text()));self.assertEqual(m['training_probabilities_before'],[.5,.5]);self.assertLess(t.probability(m['weights'],[1,-1,.1,.95]),.25);self.assertGreater(t.probability(m['weights'],[1,1,.1,.95]),.75);self.assertFalse(m['promotion']);self.assertEqual(m['full_game_admissions'],0)
 def test_heldout_never_trains(self):
  self.review['purpose']='heldout';self.write_review()
  with self.assertRaises(ValueError):t.train(self.root,self.root/'model')
 def test_unreviewed_experience_rejected(self):
  for key,value in [('reviewer',''),('findings',[]),('unresolved_in_scope',['unknown']),('labels',{})]:
   with self.subTest(key=key):
    old=self.review[key];self.review[key]=value;self.write_review()
    with self.assertRaises(ValueError):t.train(self.root,self.root/'model')
    self.review[key]=old
 def test_changed_data_or_engine_log_rejected(self):
  for name in ('decisions.jsonl','engine.log'):
   p=self.root/name;old=p.read_bytes();p.write_bytes(old+b'changed')
   with self.assertRaises(ValueError):t.train(self.root,self.root/'model')
   p.write_bytes(old)
 def test_rehashed_data_must_match_engine_rows(self):
  p=self.root/'decisions.jsonl';p.write_text(p.read_text().replace('0.3','0.4'));self.review['data_sha256']=t.sha(p);self.write_review()
  with self.assertRaises(ValueError):t.train(self.root,self.root/'model')
 def test_frozen_model_and_duplicate_ids_preserved(self):
  out=self.root/'model';t.train(self.root,out);before=out.read_bytes()
  with self.assertRaises(FileExistsError):t.train(self.root,out)
  self.assertEqual(out.read_bytes(),before);self.rows[1]['id']='0';self.save()
  with self.assertRaises(ValueError):t.train(self.root,self.root/'other')
if __name__=='__main__':unittest.main()
