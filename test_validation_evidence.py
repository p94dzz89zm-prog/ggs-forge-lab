"""A partial run must not report scheduled suites as completed checks."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('recovery_runner',Path(__file__).parent/'forge-fork/run_pilot_recovery.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class PartialValidationEvidence(unittest.TestCase):
    def test_failure_and_unstarted_suites_not_counted(self):
        rows=[{'suite':'RandomCombatReferee','expected':128,'passed':True},
              {'suite':'CounterFamilyRegression','expected':28,'passed':False}]
        self.assertEqual(runner.completed_evidence(rows),{'suites_attempted':2,'suites_passed':1,'check_groups_passed':128,'randomized_positions_passed':128})
    def test_no_run_is_zero_completed(self):
        self.assertEqual(runner.completed_evidence([])['check_groups_passed'],0)

if __name__=='__main__':unittest.main()
