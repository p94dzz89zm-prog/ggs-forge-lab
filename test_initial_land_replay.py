import unittest
from decision_tape import encode, START, MULLIGAN, PRIORITY


class InitialLandEncodingTest(unittest.TestCase):
    def test_initial_player_and_mulligan_choices_bind_domains(self):
        entry = {'hook': 'forge/ai/PlayerControllerAi' + START, 'call_id': 1, 'receiver': {'player_id': 0}, 'arguments': [True], 'turn': 0, 'phase': 'null', 'replay_initial_player_ids': [0, 1, 2, 3]}
        ret = {'arguments_after': [True], 'result': {'player_id': 2, 'lost': False}}
        self.assertEqual(encode(entry, ret, 0, 1, 2)['decision_type'], 'starting_player')
        ret['result']['player_id'] = 99
        self.assertEqual(encode(entry, ret, 0, 1, 2)['kind'], 'unsupported_decision')
        entry.update(hook='forge/ai/PlayerControllerAi' + MULLIGAN, arguments=[{'player_id': 0}, 0])
        ret = {'arguments_after': entry['arguments'], 'result': False}
        self.assertFalse(encode(entry, ret, 0, 1, 2)['keep'])
        entry['phase'] = 'MAIN1'
        self.assertEqual(encode(entry, ret, 0, 1, 2)['kind'], 'unsupported_decision')

    def test_land_shape_rejects_spells_or_nonhand_actions(self):
        ability = {'api': 'null', 'parameters': {}, 'pay_costs': 'no cost', 'spell': False, 'activated': False, 'trigger': False, 'x': None, 'targets': [], 'paying_mana': [], 'alternative_costs': [], 'optional_costs': [], 'source': {'card_id': 5, 'name': 'Island', 'owner_id': 0, 'zone': 'Hand'}}
        entry = {'hook': 'forge/ai/PlayerControllerAi' + PRIORITY, 'call_id': 1, 'receiver': {'player_id': 0}, 'arguments': [], 'turn': 1, 'phase': 'MAIN1', 'priority_player_id': 0, 'turn_player_id': 0}
        ret = {'arguments_after': [], 'result': [ability]}
        self.assertEqual(encode(entry, ret, 0, 1, 2)['decision_type'], 'play_land')
        ability['spell'] = True
        self.assertEqual(encode(entry, ret, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
