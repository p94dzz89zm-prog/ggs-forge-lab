import unittest
from prospective_binding import HOUSE
from prospective_certification import diagnostic_gate

class DiagnosticLaunchGateTests(unittest.TestCase):
    def report(self):return dict(construction_checks_passed=True,decks_verified=4,configuration=dict(HOUSE))
    def test_verified_capture_may_run_without_complete_game_approval(self):
        r=diagnostic_gate(dict(HOUSE),self.report(),'a','a')
        self.assertTrue(r['can_launch_natural_diagnostic']);self.assertFalse(r['complete_game_certified']);self.assertFalse(r['training_eligible'])
    def test_changed_runtime_or_deck_report_blocks(self):
        for report,actual in [({},'a'),(dict(self.report(),decks_verified=3),'a'),(self.report(),'b')]:
            self.assertFalse(diagnostic_gate(dict(HOUSE),report,actual,'a')['can_launch_natural_diagnostic'])
    def test_house_profile_cannot_silently_be_standard(self):
        for key,value in [('commander_damage_loss',True),('free_seven_reshuffles',1),('starting_life',20)]:
            config=dict(HOUSE);config[key]=value
            self.assertFalse(diagnostic_gate(config,self.report(),'a','a')['can_launch_natural_diagnostic'])

if __name__=='__main__':unittest.main()
