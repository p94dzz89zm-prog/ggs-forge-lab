"""Synthetic process-boundary contracts, not empirical gameplay evidence."""
import json,tempfile,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import evaluation_batch as e
class PairCheckpointResumeTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name);self.jar=self.root/'engine.jar'
  with zipfile.ZipFile(self.jar,'w') as z:z.writestr('fixture','synthetic')
  (self.root/'decks').mkdir()
  for n in ['GGS_Apex_20261017_v1','Jaymie_Ezio','Gabe_Food','Destyn_Turtles']:(self.root/'decks'/(n+'.dck')).write_text('synthetic input')
  ai=self.root/'res/ai';ai.mkdir(parents=True)
  (ai/'Default.ai').write_text('synthetic');self.calls=[]
  self.a=SimpleNamespace(baseline=self.jar,candidate=self.jar,output=self.root/'pair',engine=self.root,population='stock',deck='GGS_Apex_20261017_v1',purpose='development',seed=123,rotation=0,timeout=1,max_new_games=1)
  self.a.source_commit='1'*40
  def batch(engine,jar,out,*args,**kwargs):
   self.calls.append(out.name);return [{'seed':123,'status':'completed','winner':'synthetic','engine_ms':1,'seats':['a','b','c','d']}]
  for target,value in [('evaluation_batch.dragonmind.ROOT',self.root),('evaluation_batch.dragonmind.batch',batch),('evaluation_batch.inspect',lambda root:[{'record_integrity_passed':True}]),('evaluation_batch.assess',lambda *a:{'status':'pending_review'})]:
   p=patch(target,value);p.start();self.addCleanup(p.stop)
 def test_each_side_can_be_saved_then_resumed_without_replay(self):
  self.assertEqual(e.run(self.a),0);self.assertEqual(self.calls,['baseline']);self.assertFalse(json.loads((self.a.output/'summary.json').read_text())['all_completed'])
  self.assertEqual(e.run(self.a),0);self.assertEqual(self.calls,['baseline','candidate']);self.assertTrue(json.loads((self.a.output/'summary.json').read_text())['all_completed'])
  self.assertEqual(e.run(self.a),0);self.assertEqual(self.calls,['baseline','candidate'])
 def test_unknown_inflight_side_never_relaunched(self):
  e.run(self.a);p=self.a.output/'state.json';s=json.loads(p.read_text());s['attempts'].append({'label':'candidate','status':'running'});p.write_text(json.dumps(s))
  with self.assertRaises(RuntimeError):e.run(self.a)
  self.assertEqual(self.calls,['baseline'])
 def test_capture_failure_is_saved_and_blocks_candidate_and_retry(self):
  with patch('evaluation_batch.capture',side_effect=OSError('synthetic disk failure')):
   self.assertEqual(e.run(self.a),1)
  s=json.loads((self.a.output/'state.json').read_text());self.assertFalse(s['attempts'][0]['complete']);self.assertEqual(s['attempts'][0]['status'],'capture_failed')
  with self.assertRaises(ValueError):e.run(self.a)
  self.assertEqual(self.calls,['baseline'])
 def test_missing_capture_blocks_resume_without_recapture(self):
  e.run(self.a);(self.a.output/'captures/baseline.zip').unlink()
  with self.assertRaises(OSError):e.run(self.a)
  self.assertEqual(self.calls,['baseline'])
 def test_publication_interruption_retains_unknown_side_and_orphan_capture(self):
  original=e.atomic_json
  def interrupt(path,state):
   if path.name=='state.json' and state.get('attempts') and state['attempts'][0].get('immutable_capture'):raise OSError('synthetic interrupted journal save')
   original(path,state)
  with patch('evaluation_batch.atomic_json',interrupt):
   with self.assertRaises(OSError):e.run(self.a)
  self.assertTrue((self.a.output/'captures/baseline.zip').exists())
  with self.assertRaises(RuntimeError):e.run(self.a)
  self.assertEqual(self.calls,['baseline'])
