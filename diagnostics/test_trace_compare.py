import unittest
from trace_compare import read_games, compare

RESULT = 'DragonMind Result: {"seed":1,"status":"completed","winner":"Ai(1)","last_logged_turn":1}\n'

class TraceComparisonTest(unittest.TestCase):
    def audit(self, a, b):
        return compare(read_games(a + RESULT)[1], read_games(b + RESULT)[1])

    def test_multiline_block_order_is_visible_but_inventory_equal(self):
        a = "Phase: Blockers\nCombat: Ai(2) assigned Bear (2) to block Dragon (3).\nAi(2) didn't block Ninja (4).\n"
        b = "Phase: Blockers\nCombat: Ai(2) didn't block Ninja (4).\nAi(2) assigned Bear (2) to block Dragon (3).\n"
        result = self.audit(a, b)
        self.assertFalse(result['trace_match'])
        self.assertTrue(result['phase_inventory_match'])
        self.assertEqual(result['full_tracked_records'], 3)

    def test_changed_block_target_and_damage_amount_are_rejected(self):
        a = "Phase: Damage\nCombat: Ai(2) assigned Bear (2) to block Dragon (3).\nDamage: Bear (2) deals 2 damage to Dragon (3).\n"
        self.assertFalse(self.audit(a, a.replace('to block Dragon (3)', 'to block Ninja (4)'))['phase_inventory_match'])
        self.assertFalse(self.audit(a, a.replace('deals 2', 'deals 3'))['phase_inventory_match'])

    def test_phase_and_stack_order_are_preserved(self):
        a = "Phase: First\nAdd To Stack: A\nAdd To Stack: B\nDamage: A deals 2 damage.\nPhase: Second\n"
        b = "Phase: First\nAdd To Stack: B\nAdd To Stack: A\nDamage: A deals 2 damage.\nPhase: Second\n"
        self.assertFalse(self.audit(a, b)['phase_inventory_match'])
        b = "Phase: First\nAdd To Stack: A\nAdd To Stack: B\nPhase: Second\nDamage: A deals 2 damage.\n"
        self.assertFalse(self.audit(a, b)['phase_inventory_match'])

if __name__ == '__main__':
    unittest.main()
