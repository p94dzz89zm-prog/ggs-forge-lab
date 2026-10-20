import copy,unittest
from decision_tape import encode,TRIGGER_STACK

class FoodTriggerEncodingTest(unittest.TestCase):
    def test_sam_food_requires_untargeted_own_combat_and_no_effect_rng(self):
        ability=dict(ability_id=7,source=dict(card_id=101,name='Sam, Loyal Attendant',controller_id=0,zone='Battlefield'),api='Token',parameters={},trigger=True,spell=False,x=None,pay_costs='{0}',targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        event=dict(sa=dict(ability_id=7,description='At the beginning of combat on your turn, create a Food token.'),si=dict(source=dict(view_id=101),activating_player=dict(view_id=0),target_cards=[],target_players=[]))
        entry=dict(hook='forge/ai/PlayerControllerAi'+TRIGGER_STACK,call_id=1,receiver=dict(player_id=0),arguments=[[ability]],turn=9,phase='COMBAT_BEGIN',priority_player_id=0,turn_player_id=0,replay_trigger_order=[ability],replay_trigger_announcements=[event],replay_trigger_zero_payments=1)
        returned=dict(result=None,arguments_after=copy.deepcopy(entry['arguments']))
        self.assertEqual(encode(entry,returned,0,1,2)['decision_type'],'sam_food_trigger_stack')
        for key,value in [('phase','MAIN1'),('turn_player_id',1),('replay_trigger_unknown_rng',1),('replay_trigger_effect_calls',1)]:
            wrong=copy.deepcopy(entry);wrong[key]=value
            self.assertEqual(encode(wrong,returned,0,1,2)['kind'],'unsupported_decision')
        event['si']['target_players']=[dict(view_id=1)]
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
