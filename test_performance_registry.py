import tempfile,unittest,json,hashlib
from pathlib import Path
from performance_registry import connect,record,import_technical
class EvidenceRegistryTests(unittest.TestCase):
 def test_idempotent_import_and_changed_evidence_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'metrics.sqlite';db=connect(p);record(db,'one','game',18,'a'*64,{'won':False},'b'*64);record(db,'one','game',18,'a'*64,{'won':False},'b'*64);self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
   with self.assertRaises(ValueError):record(db,'one','game',18,'a'*64,{'won':True},'c'*64)
   db.close();db=connect(p);self.assertIn('false',db.execute('SELECT data FROM events').fetchone()[0]);db.close()

 def test_truncated_saved_log_is_not_trusted_from_summary_alone(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);log=root/'Suite.log';log.write_text('Checks passed: 1\n');expected=hashlib.sha256(log.read_bytes()).hexdigest();(root/'validation.json').write_text(json.dumps({'jar_sha256':'a'*64,'all_passed':True,'suites':[{'suite':'Suite','passed':True,'expected':1,'log_sha256':expected}],'completed_evidence':{'check_groups_passed':1}}));db=connect(root/'m.sqlite');log.write_text('startup only\n')
   with self.assertRaisesRegex(ValueError,'log changed'):import_technical(db,root,17)
   self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],0);db.close()
 def test_matching_hash_without_exact_marker_cannot_enter_dashboard(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);log=root/'Suite.log';log.write_text('Checks passed: 2\n');(root/'validation.json').write_text(json.dumps({'jar_sha256':'a'*64,'all_passed':True,'suites':[{'suite':'Suite','passed':True,'expected':1,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}],'completed_evidence':{'check_groups_passed':1}}));db=connect(root/'m.sqlite')
   with self.assertRaisesRegex(ValueError,'completion marker'):import_technical(db,root,17)
   db.close()
