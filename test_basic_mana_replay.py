import copy
import unittest
from decision_tape import encode, PAYMENT


class BasicManaEncodingTest(unittest.TestCase):
    def test_actual_operations_and_selector_only_randomness_required(self):
        unit = dict(color='U', source_card_id=2, snow=False, restricted=False)
        ability = dict(api='PermanentNoncreature', parameters={}, spell=True, x=None, targets=[],
                       paying_mana=[], alternative_costs=[], optional_costs=[], ability_id=4,
                       source=dict(card_id=1, commander=False, zone='Stack'))
        args = ['{1}', ability, None, None, False]
        entry = dict(hook='forge/game/player/PlayerController'+PAYMENT, call_id=1,
                     receiver=dict(player_id=0), arguments=args, mana_context=dict(pool=[]),
                     replay_payment_random_requests=1,
                     replay_payment_operations=[dict(op='activate_basic', card_id=2, valid=True), dict(op='spend', mana=unit)])
        returned = dict(result=True, arguments_after=copy.deepcopy(args))
        returned['arguments_after'][1]['paying_mana'] = [unit]
        self.assertEqual(encode(entry, returned, 0, 1, 2)['decision_type'], 'basic_land_mana')
        entry['replay_payment_unknown_random_requests'] = 1
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')
        entry.pop('replay_payment_unknown_random_requests')
        entry['replay_payment_operations'][0]['valid'] = False
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')

    def test_sol_ring_partial_spend_preserves_production_choice(self):
        unit = dict(color='C', source_card_id=2, snow=False, restricted=False)
        ability = dict(api='PermanentNoncreature', parameters={}, spell=True, x=None, targets=[],
                       paying_mana=[], alternative_costs=[], optional_costs=[], ability_id=4,
                       source=dict(card_id=1, commander=False, zone='Stack'))
        args = ['{1}', ability, None, None, False]
        entry = dict(hook='forge/game/player/PlayerController'+PAYMENT, call_id=1,
                     receiver=dict(player_id=0), arguments=args, mana_context=dict(pool=[]),
                     replay_payment_operations=[dict(op='activate_basic', card_id=2, card_name='Sol Ring', valid=True, parameters=dict(Amount='2')),
                                                dict(op='spend', mana=unit)])
        returned = dict(result=True, arguments_after=copy.deepcopy(args))
        returned['arguments_after'][1]['paying_mana'] = [unit]
        row = encode(entry, returned, 0, 1, 2)
        self.assertEqual(row['decision_type'], 'fixed_tap_mana')
        self.assertEqual(row['operations'][0]['parameters']['Amount'], '2')
        entry['replay_payment_operations'].append(dict(op='spend', mana=unit, expected_success=False))
        row = encode(entry, returned, 0, 1, 2)
        self.assertEqual(row['decision_type'], 'fixed_tap_mana')
        self.assertFalse(row['operations'][-1]['expected_success'])
        entry['replay_payment_operations'][0]['valid'] = False
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')

    def test_commander_color_production_requires_actual_recorded_choice(self):
        unit = dict(color='B', source_card_id=2, snow=False, restricted=False)
        ability = dict(api='PermanentCreature', parameters={}, spell=True, x=None, targets=[],
                       paying_mana=[], alternative_costs=[], optional_costs=[], ability_id=4,
                       prior_commander_casts=0, source=dict(card_id=1, commander=True, zone='Stack'))
        args = ['{B}', ability, None, None, False]
        operation = dict(op='activate_basic', card_id=2, card_name='Command Tower', valid=True,
                         parameters=dict(Produced='Combo ColorIdentity'))
        entry = dict(hook='forge/game/player/PlayerController'+PAYMENT, call_id=1,
                     receiver=dict(player_id=0), arguments=args, mana_context=dict(pool=[]),
                     replay_payment_operations=[operation, dict(op='spend', mana=unit)])
        returned = dict(result=True, arguments_after=copy.deepcopy(args))
        returned['arguments_after'][1]['paying_mana'] = [unit]
        self.assertEqual(encode(entry, returned, 0, 1, 2)['reason'], 'missing_selected_mana_color')
        operation['color_choice'] = dict(selected_color='B', selected_mask=4)
        row = encode(entry, returned, 0, 1, 2)
        self.assertEqual(row['decision_type'], 'selected_tap_mana')
        self.assertEqual(row['commander_tax'], 0)
        ability['prior_commander_casts'] = None
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
