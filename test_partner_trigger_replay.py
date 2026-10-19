import copy
import unittest
from decision_tape import encode, TRIGGER_STACK


class PartnerTriggerEncodingTest(unittest.TestCase):
    def test_target_announcement_order_and_effect_rng_required(self):
        ability = dict(ability_id=7, source=dict(card_id=4, name='Frodo, Adventurous Hobbit'),
                       api='ChangeZone', trigger=True, spell=False, x=None, pay_costs='{0}',
                       targets=[], paying_mana=[], alternative_costs=[], optional_costs=[])
        event = dict(sa=dict(ability_id=7), si=dict(source=dict(view_id=4),
                     activating_player=dict(view_id=0), target_cards=[], target_players=[dict(view_id=0)]))
        entry = dict(hook='forge/ai/PlayerControllerAi'+TRIGGER_STACK, call_id=1,
                     receiver=dict(player_id=0), arguments=[[ability]], turn=1, phase='MAIN2',
                     priority_player_id=0, turn_player_id=0, replay_trigger_order=[ability],
                     replay_trigger_announcements=[event], replay_trigger_zero_payments=1)
        returned = dict(result=None, arguments_after=copy.deepcopy(entry['arguments']))
        self.assertEqual(encode(entry, returned, 0, 1, 2)['target_player_ids'], [0])
        entry['replay_trigger_unknown_rng'] = 1
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')
        entry['replay_trigger_unknown_rng'] = 0
        event['si']['target_cards'] = [dict(view_id=9)]
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')
        event['si']['target_cards'] = []
        entry['replay_trigger_order'] = []
        self.assertEqual(encode(entry, returned, 0, 1, 2)['kind'], 'unsupported_decision')


if __name__ == '__main__':
    unittest.main()
