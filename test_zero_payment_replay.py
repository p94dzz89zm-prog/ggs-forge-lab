import unittest
from decision_tape import encode, PAYMENT


class ZeroPaymentEncodingTest(unittest.TestCase):
    def test_zero_component_requires_zero_only_unchanged_effect(self):
        ability = {'ability_id': 4, 'source': {'card_id': 2}, 'api': 'Draw',
                   'parameters': {}, 'pay_costs': '{0}', 'x': None,
                   'paying_mana': [], 'alternative_costs': [], 'optional_costs': []}
        args = ['{0}', ability, None, None, True]
        entry = {'hook': 'forge/game/player/PlayerController' + PAYMENT,
                 'call_id': 1, 'receiver': {'player_id': 0}, 'arguments': args}
        returned = {'arguments_after': args, 'result': True}
        self.assertEqual(encode(entry, returned, 0, 1, 2)['decision_type'], 'zero_effect_mana')
        for key, value in [('pay_costs', '{T}, Sacrifice CARDNAME'), ('x', 0),
                           ('paying_mana', ['G']), ('parameters', {'Announce': 'NumTimes'})]:
            before = ability[key]; ability[key] = value
            self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')
            ability[key] = before
        args[4] = False
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
