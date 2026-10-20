import copy
import unittest
from replay_identity_audit import compare

class IdentityAuditTest(unittest.TestCase):
    def test_mismatch_is_reported_and_ambiguous_or_changed_birth_rejected(self):
        original=dict(record=10,engine_card_id=412,cause=dict(source=242,ordinal=1),characteristics=dict(name='Bird Token',owner=3,controller=3,power=2,toughness=2))
        actual=copy.deepcopy(original);actual.update(record=8,engine_card_id=406)
        report=compare([original],[actual]);self.assertFalse(report['complete_state_reconstruction']);self.assertFalse(report['driver_aliases_installed']);self.assertEqual(len(report['unresolved_engine_id_discrepancies']),1)
        with self.assertRaisesRegex(ValueError,'Duplicate'):compare([original,original],[actual,actual])
        actual['characteristics']['owner']=2
        with self.assertRaisesRegex(ValueError,'alias forbidden'):compare([original],[actual])

if __name__=='__main__':unittest.main()
