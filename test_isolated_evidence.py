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
class CollectorIsolationTests(unittest.TestCase):
 def test_direct_managed_workspace_run_is_rejected_before_engine_use(self):
  from types import SimpleNamespace
  from evaluation_batch import run
  with self.assertRaisesRegex(ValueError,'Live evidence'):
   run(SimpleNamespace(output=Path('/workspace/never-create-live-game')))
 def test_cli_routes_child_to_external_placeholder_and_retains_allocation(self):
  from types import SimpleNamespace
  from unittest.mock import patch
  from evaluation_batch import run_isolated_cli
  with tempfile.TemporaryDirectory() as td:
   a=SimpleNamespace(output=Path(td)/'allocation',source_commit='a'*40,timeout=120,max_new_games=1)
   with patch('isolated_evidence.run',return_value={'producer':{'stage_complete':True}}) as call:
    self.assertEqual(run_isolated_cli(a,['--output','original','--seed','42']),0)
    cmd=call.call_args.args[0];self.assertEqual(cmd[cmd.index('--output')+1],'{output}/pair');self.assertIn('42',cmd)
   self.assertTrue((a.output/'isolated-stage.json').exists())
   with self.assertRaises(FileExistsError):run_isolated_cli(a,['--output','original','--seed','42'])

if __name__=='__main__':unittest.main()
