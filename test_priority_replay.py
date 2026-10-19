import unittest
from decision_tape import PRIORITY, encode


class PriorityReplayEncodingTest(unittest.TestCase):
    def fixture(self):
        entry = {'hook': 'forge/ai/bridge/PlayerControllerBridge' + PRIORITY,
                 'arguments': [], 'call_id': 1, 'receiver': {'player_id': 2, 'lost': False},
                 'priority_player_id': 2, 'turn_player_id': 0, 'turn': 5, 'phase': 'MAIN1',
                 'mana_context': {'pool': []}}
        returned = {'result': None, 'arguments_after': []}
        return entry, returned

    def test_pass_retains_live_context_and_selected_action_stays_unsupported(self):
        entry, result = self.fixture()
        row = encode(entry, result, 8, 10, 11)
        self.assertEqual(row['kind'], 'decision')
        self.assertEqual(row['context'], {'turn': 5, 'phase': 'MAIN1', 'priority_player_id': 2, 'turn_player_id': 0})
        self.assertTrue(row['empty_mana_pool'])
        result['result'] = [{'ability_id': 5}]
        self.assertEqual(encode(entry, result, 8, 10, 11)['reason'], 'selected_ability_requires_choices_and_mutations')

    def test_pass_rejects_missing_priority_forbidden_phase_and_unannounced_mana(self):
        for key, value in [('priority_player_id', 1), ('phase', 'UNTAP'), ('mana_context', {'pool': [{'color': 'R'}]})]:
            entry, result = self.fixture(); entry[key] = value
            self.assertEqual(encode(entry, result, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
