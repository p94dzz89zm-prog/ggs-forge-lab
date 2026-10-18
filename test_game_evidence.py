import copy,json,tempfile,unittest
from pathlib import Path
from game_evidence import verify,sha
class EvidenceWriterContracts(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.d=self.root/'engine-records/game';self.d.mkdir(parents=True);self.a=self.root/'audit/game';self.a.mkdir(parents=True)
  result=b'{"status":"completed"}';text=b'event\nDragonMind Result: {"status":"completed"}\n';(self.d/'1.json').write_bytes(result);(self.d/'1.log').write_bytes(text)
  self.m={'format':1,'seed':1,'game_id':'g','write_status':'complete','completion_marker':'DRAGONMIND_EVIDENCE_COMPLETE','transcript_sha256':sha(text),'transcript_records':2,'result_sha256':sha(result),'streams':[]}
  for seat in range(4):
   row={'evidence_game_id':'g','stream_sequence':1,'state':{'viewer_id':seat,'players':[{'id':seat,'hand':[],'battlefield':[{'owner_id':seat,'controller_id':seat,'zone':'Battlefield'}]}]}}
   data=(json.dumps(row)+'\n').encode();p=self.a/f'seat-{seat}.jsonl';p.write_bytes(data);receipt={'game_id':'g','file':str(p.relative_to(self.root)),'write_status':'complete','bytes':len(data),'records':1,'sha256':sha(data)};self.m['streams'].append(receipt);self.receipt(p,receipt)
  self.save()
 def receipt(self,p,r):p.with_name(p.name+'.receipt.json').write_text(json.dumps(r))
 def save(self):(self.d/'1.evidence.json').write_text(json.dumps(self.m))
 def check(self):return verify(self.root,self.d,1)
 def change_row(self,change):
  p=self.a/'seat-0.jsonl';row=json.loads(p.read_text());change(row);data=(json.dumps(row)+'\n').encode();p.write_bytes(data);r=self.m['streams'][0];r.update(bytes=len(data),sha256=sha(data));self.receipt(p,r);self.save()
 def test_complete(self):self.assertTrue(self.check()['passed'])
 def test_valid_json_prefix_truncation_rejected(self):
  p=self.a/'seat-0.jsonl';p.write_bytes(b'{}\n')
  with self.assertRaises(ValueError):self.check()
 def test_record_count_rejected_even_if_hash_matches(self):
  self.m['streams'][0]['records']=2;self.receipt(self.a/'seat-0.jsonl',self.m['streams'][0]);self.save()
  with self.assertRaises(ValueError):self.check()
 def test_missing_completion_rejected(self):
  self.m['write_status']='interrupted';self.save()
  with self.assertRaises(ValueError):self.check()
 def test_cross_game_row_rejected(self):
  self.change_row(lambda r:r.update(evidence_game_id='other'))
  with self.assertRaises(ValueError):self.check()
 def test_missing_owner_rejected(self):
  self.change_row(lambda r:r['state']['players'][0]['battlefield'][0].pop('owner_id'))
  with self.assertRaises(ValueError):self.check()
 def test_partial_rejected(self):
  (self.a/'unfinished.jsonl.partial').write_text('{}')
  with self.assertRaises(ValueError):self.check()
 def test_unsafe_path_rejected(self):
  self.m['streams'][0]['file']='../outside';self.save()
  with self.assertRaises(ValueError):self.check()
 def test_missing_receipt_rejected(self):
  (self.a/'seat-0.jsonl.receipt.json').unlink()
  with self.assertRaises(FileNotFoundError):self.check()
class ReceiptDiscoveryTests(unittest.TestCase):
 def test_referee_ignores_writer_receipt_json(self):
  from referee_games import inspect
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);d=root/'engine-records/game';d.mkdir(parents=True)
   result={'seed':1,'status':'completed','winner':'A','engine_ms':1};(d/'1.json').write_text(json.dumps(result));(d/'1.log').write_text('DragonMind Result: '+json.dumps(result)+'\n');(d/'1.evidence.json').write_text('{"writer_receipt":true}')
   reports=inspect(root);self.assertEqual(len(reports),1);self.assertTrue(reports[0]['record_integrity_passed'])

if __name__=='__main__':unittest.main()
