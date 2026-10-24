import copy
import unittest
from decision_tape import encode, PRIORITY, SWAN_PARAMETERS

class SwanEncodingTest(unittest.TestCase):
    def test_public_announced_target_required_and_ambiguity_rejected(self):
        source=dict(card_id=242,name='Swan Song',zone='Hand',owner_id=2,mana_cost='{U}')
        ability=dict(source=source,ability_id=1525,api='Counter',parameters=copy.deepcopy(SWAN_PARAMETERS),spell=True,activated=False,trigger=False,x=None,targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        hint=dict(card_id=381,name='Rampant Growth',source_record=15114,basis='public stack target choice')
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+PRIORITY,call_id=1,receiver=dict(player_id=2),arguments=[],turn=8,phase='MAIN1',priority_player_id=2,turn_player_id=3,replay_counter_announcements={'242:1525':[hint]})
        returned=dict(result=[ability],arguments_after=[])
        self.assertEqual(encode(entry,returned,0,1,2)['target_spell_card_id'],381)
        entry['replay_counter_announcements']={}
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        entry['replay_counter_announcements']={'242:1525':[hint,hint]}
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        entry['replay_counter_announcements']={'242:1525':[hint]};ability['x']=1
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
