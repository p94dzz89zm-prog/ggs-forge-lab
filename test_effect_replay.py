import copy
import unittest
from decision_tape import COLORS, COUNTER, REPLACEMENT, encode


class EffectReplayEncodingTest(unittest.TestCase):
    def encode(self, hook, args, result):
        return encode({'hook': 'forge/ai/PlayerControllerAi' + hook, 'call_id': 1,
                       'receiver': {'player_id': 0}, 'arguments': args},
                      {'arguments_after': copy.deepcopy(args), 'result': result}, 0, 1, 2)

    def test_replacement_is_offered_unique_identity_not_recorded_outcome(self):
        item = {'trait_type': 'ReplaceMoved', 'source': {'card_id': 4}, 'parameters': {'Event': 'Moved'}}
        good = self.encode(REPLACEMENT, [[item]], item)
        self.assertEqual(good['decision_type'], 'replacement_choice')
        self.assertEqual(good['selected_effect']['source_card_id'], 4)
        self.assertEqual(self.encode(REPLACEMENT, [[item, item]], item)['kind'], 'unsupported_decision')
        other = copy.deepcopy(item); other['source']['card_id'] = 5
        self.assertEqual(self.encode(REPLACEMENT, [[item]], other)['kind'], 'unsupported_decision')

    def test_counter_selection_requires_membership_and_parameter_binding(self):
        args = [['P1P1'], None, 'counter', {'Target': None}]
        self.assertEqual(self.encode(COUNTER, args, 'P1P1')['decision_type'], 'counter_choice')
        self.assertEqual(self.encode(COUNTER, args, 'M1M1')['kind'], 'unsupported_decision')
        args[3]['Target'] = {'card_id': 4}
        self.assertEqual(self.encode(COUNTER, args, 'P1P1')['kind'], 'unsupported_decision')

    def test_color_choice_preserves_exclusions_and_cardinality(self):
        args = ['choose', None, 1, 1, 'WUBR']
        self.assertEqual(self.encode(COLORS, args, 'B')['decision_type'], 'color_choice')
        for value in ['G', 'WB', 'C']:
            self.assertEqual(self.encode(COLORS, args, value)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
