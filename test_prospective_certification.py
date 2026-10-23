import unittest
from prospective_opening_audit import JavaRandom, bounded, permutation, audit, snapshot_objects
from prospective_certification import gate

class ProspectiveCertificationTests(unittest.TestCase):
    def test_java_random_known_vector(self):
        self.assertEqual(JavaRandom(0).bits(31),1569741360)
        self.assertEqual(JavaRandom(58).bits(31),1565509122)
    def test_power_two_and_rejection_sampling(self):
        self.assertEqual(bounded(iter([(31,1565509122)]),4),2)
        self.assertEqual(bounded(iter([(31,2147483647),(31,7)]),3),1)
    def test_shuffle_exact_expected_small_vector(self):
        self.assertEqual(permutation(['a','b','c'],[(31,5),(31,0)]),['b','a','c'])
    def test_shuffle_missing_or_extra_bits_rejected(self):
        for rows in [[],[(32,5),(31,0)],[(31,5),(31,0),(31,1)]]:
            with self.assertRaises(ValueError):permutation(['a','b','c'],rows)
    def test_incomplete_prefix_never_approved(self):
        with self.assertRaises(ValueError):audit([],58)
    def test_playable_view_references_do_not_duplicate_physical_objects(self):
        c={'id':1,'name':'fixture','owner':0,'commander':True}
        self.assertEqual(len(snapshot_objects({'players':[{'Command':[c],'Flashback':[dict(c)]}]})),1)
        with self.assertRaises(ValueError):snapshot_objects({'players':[{'Command':[c],'Library':[dict(c)]}]})
    def test_unbound_virtual_reference_rejected(self):
        c={'id':1,'name':'fixture','owner':0,'commander':True}
        with self.assertRaises(ValueError):snapshot_objects({'players':[{'Flashback':[c]}]})
    def test_capture_claim_cannot_open_certification_gate(self):
        for config in [{},{'all_verified':True},{'players':4,'starting_life':40,'free_seven_reshuffles':3,'commander_damage_loss':False,'profile':'ggs-house-v1'}]:
            result=gate(config);self.assertFalse(result['can_start_full_certification_game']);self.assertFalse(result['training_eligible'])

if __name__=='__main__':unittest.main()
