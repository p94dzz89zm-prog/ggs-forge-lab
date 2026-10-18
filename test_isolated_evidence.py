import json
from pathlib import Path
import sys
import tempfile
import unittest
import isolated_evidence as isolation

class IsolationTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.archive=self.root/'out.zip'
 def run_stage(self,code):return isolation.run([sys.executable,'-c',code,'{output}'],self.archive,'a'*40,scratch_base=self.root/'outside',timeout=10)
 def test_verified_transport_restores_fresh_and_retains_original(self):
  r=self.run_stage("import pathlib,sys;pathlib.Path(sys.argv[1],'record.json').write_text('{\"done\":true}')")
  self.assertTrue(r['producer']['stage_complete']);self.assertTrue(Path(r['isolated_root']).exists())
  restored=isolation.restore(self.archive,r['sha256'],self.root/'restored')
  self.assertEqual(json.loads((restored/'output/record.json').read_text()),{'done':True})
  self.assertFalse(r['producer']['rules_approval'])
 def test_failed_producer_retained_without_completion_or_admission(self):
  r=self.run_stage("import pathlib,sys;pathlib.Path(sys.argv[1],'unfinished.partial').write_text('prefix');sys.exit(7)")
  self.assertFalse(r['producer']['stage_complete']);self.assertFalse(r['producer']['learning_admission']);self.assertTrue((Path(r['isolated_root'])/'output/unfinished.partial').exists())
 def test_workspace_root_rejected(self):
  with self.assertRaises(ValueError):isolation.run([sys.executable,'-c','pass','{output}'],self.archive,'a'*40,scratch_base='/workspace/unsafe')
 def test_existing_archive_never_replaced(self):
  self.archive.write_text('original')
  with self.assertRaises(FileExistsError):self.run_stage('pass')
  self.assertEqual(self.archive.read_text(),'original')
 def test_changed_archive_refuses_restore(self):
  r=self.run_stage('pass');self.archive.write_bytes(self.archive.read_bytes()[:-20])
  with self.assertRaises(ValueError):isolation.restore(self.archive,r['sha256'],self.root/'restore')
if __name__=='__main__':unittest.main()
