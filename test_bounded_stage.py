import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).parent/'.github/scripts/bounded_stage.py'
class BoundedStageTests(unittest.TestCase):
    def run_stage(self, directory, seconds, code):
        return subprocess.run([sys.executable,str(SCRIPT),'--stage','probe','--seconds',str(seconds),'--',sys.executable,'-c',code],
                              cwd=directory,env={**os.environ,'GITHUB_SHA':'b'*40},capture_output=True,text=True,timeout=10)
    def test_success_and_immutable_resume(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.run_stage(d,3,"print('complete')").returncode,0)
            p=Path(d)/'ci-results/probe.json'; before=p.read_bytes()
            row=json.loads(before)
            self.assertEqual(row['status'],'passed')
            self.assertEqual(row['log_sha256'],hashlib.sha256((p.parent/'probe.log').read_bytes()).hexdigest())
            self.assertNotEqual(self.run_stage(d,3,"print('duplicate')").returncode,0)
            self.assertEqual(p.read_bytes(),before)
    def test_failed_command_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(self.run_stage(d,3,"raise AssertionError('visible failure')").returncode,0)
            root=Path(d)/'ci-results'
            self.assertEqual(json.loads((root/'probe.json').read_text())['status'],'failed')
            self.assertIn('visible failure',(root/'probe.log').read_text())
    def test_timeout_preserves_partial_log(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertNotEqual(self.run_stage(d,1,"import time; print('started',flush=True);time.sleep(10)").returncode,0)
            root=Path(d)/'ci-results'
            self.assertEqual(json.loads((root/'probe.json').read_text())['status'],'timeout')
            self.assertIn('started',(root/'probe.log').read_text())
    def test_unknown_inflight_never_replayed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'ci-results';root.mkdir()
            p=root/'probe.json';p.write_text('{"status":"running"}')
            self.assertNotEqual(self.run_stage(d,3,"print('must not execute')").returncode,0)
            self.assertEqual(json.loads(p.read_text())['status'],'running')
            self.assertFalse((root/'probe.log').exists())
if __name__=='__main__': unittest.main()
