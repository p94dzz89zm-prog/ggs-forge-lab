import copy
import unittest
from decision_tape import encode, PRIORITY, RAMPANT_PARAMETERS

class RampantEncodingTest(unittest.TestCase):
    def test_fixed_targetless_sorcery_selection_requires_exact_definition(self):
        source=dict(card_id=5,name='Rampant Growth',zone='Hand',owner_id=0,mana_cost='{1}{G}')
        ability=dict(source=source,ability_id=7,api='ChangeZone',parameters=copy.deepcopy(RAMPANT_PARAMETERS),spell=True,activated=False,trigger=False,x=None,targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+PRIORITY,call_id=1,receiver=dict(player_id=0),arguments=[],turn=8,phase='MAIN1',priority_player_id=0,turn_player_id=0)
        returned=dict(result=[ability],arguments_after=[])
        self.assertEqual(encode(entry,returned,0,1,2)['decision_type'],'rampant_growth_spell')
        ability['parameters']['Tapped']='False'
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        ability['parameters']=copy.deepcopy(RAMPANT_PARAMETERS);ability['targets']=[dict(player_id=1)]
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        ability['targets']=[];ability['x']=3
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
