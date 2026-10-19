import unittest
from decision_tape import encode, PRIORITY


class PlainSpellEncodingTest(unittest.TestCase):
    def test_plain_hand_spell_excludes_modes_x_and_alternative_costs(self):
        ability = {'ability_id': 4, 'api': 'PermanentNoncreature', 'parameters': {},
                   'spell': True, 'activated': False, 'trigger': False, 'x': None,
                   'targets': [], 'paying_mana': [], 'alternative_costs': [], 'optional_costs': [],
                   'source': {'card_id': 1, 'name': 'Sol Ring', 'owner_id': 0, 'zone': 'Hand', 'mana_cost': '{1}'}}
        e = {'hook': 'forge/ai/bridge/PlayerControllerBridge'+PRIORITY, 'call_id': 1,
             'receiver': {'player_id': 0}, 'arguments': [], 'priority_player_id': 0,
             'turn_player_id': 0, 'phase': 'MAIN1', 'turn': 1}
        r = {'result': [ability], 'arguments_after': []}
        self.assertEqual(encode(e, r, 0, 1, 2)['decision_type'], 'plain_hand_permanent_spell')
        for key, value in [('parameters', {'Mode': 'Choice'}), ('x', 1), ('alternative_costs', ['Freerunning'])]:
            old = ability[key]; ability[key] = value
            self.assertEqual(encode(e, r, 0, 1, 2)['kind'], 'unsupported_decision')
            ability[key] = old
        ability['source']['zone'] = 'Command'
        self.assertEqual(encode(e, r, 0, 1, 2)['kind'], 'unsupported_decision')
        ability['source']['commander'] = True
        ability['prior_commander_casts'] = 2
        row = encode(e, r, 0, 1, 2)
        self.assertEqual(row['decision_type'], 'command_permanent_spell')
        self.assertEqual(row['commander_tax'], 4)
        ability['prior_commander_casts'] = None
        self.assertEqual(encode(e, r, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
