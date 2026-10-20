"""Reproduce the observed post-suite log drift without rewriting its history."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('final_log_runner',Path(__file__).parent/'forge-fork/run_pilot_recovery.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class FinalLogIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name);self.log=self.root/'PilotRecoveryRegression.log'
        self.log.write_text('PASS final scenario\nChecks passed: 52\n')
        self.entry={'suite':'PilotRecoveryRegression','passed':True,'returncode':0,'timeout':False,
            'expected':52,'log_sha256':hashlib.sha256(self.log.read_bytes()).hexdigest()}
        self.manifest={'planned_suites':{'PilotRecoveryRegression':52},'suites':[self.entry]}

    def test_intact_completed_suite_remains_verified(self):
        self.assertEqual(runner.recheck_saved_logs(self.root,self.manifest)['status'],'verified')

    def test_observed_success_followed_by_truncation_is_quarantined(self):
        self.log.write_text('PASS earlier scenario\n')
        result=runner.recheck_saved_logs(self.root,self.manifest)
        self.assertEqual(result['status'],'quarantined')
        self.assertEqual(result['errors'][0]['reason'],'saved log hash changed')
        self.assertTrue(self.entry['passed']) # Preserve the original observation.

    def test_rehashed_wrong_or_duplicate_marker_still_fails(self):
        for text in ['Checks passed: 51\n','Checks passed: 52\nChecks passed: 52\n']:
            with self.subTest(text=text):
                self.log.write_text(text);self.entry['log_sha256']=hashlib.sha256(self.log.read_bytes()).hexdigest()
                self.assertEqual(runner.recheck_saved_logs(self.root,self.manifest)['status'],'quarantined')

    def test_missing_log_is_quarantined(self):
        self.log.unlink()
        self.assertEqual(runner.recheck_saved_logs(self.root,self.manifest)['status'],'quarantined')

    def test_missing_or_duplicate_suite_cannot_finalize(self):
        for entries in [[],[self.entry,self.entry]]:
            with self.subTest(entries=len(entries)):
                self.manifest['suites']=entries
                self.assertEqual(runner.recheck_saved_logs(self.root,self.manifest)['status'],'quarantined')

if __name__=='__main__':unittest.main()
