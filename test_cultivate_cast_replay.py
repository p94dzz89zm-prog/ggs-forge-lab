import copy,unittest
from decision_tape import encode,PRIORITY,CULTIVATE_PARAMETERS

class CultivateEncodingTest(unittest.TestCase):
    def test_exact_targetless_cultivate_selection_only(self):
        source=dict(card_id=5,name='Cultivate',zone='Hand',owner_id=0,mana_cost='{2}{G}')
        ability=dict(source=source,ability_id=7,api='ChangeZone',parameters=copy.deepcopy(CULTIVATE_PARAMETERS),spell=True,activated=False,trigger=False,x=None,targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+PRIORITY,call_id=1,receiver=dict(player_id=0),arguments=[],turn=10,phase='MAIN2',priority_player_id=0,turn_player_id=0)
        returned=dict(result=[ability],arguments_after=[])
        self.assertEqual(encode(entry,returned,0,1,2)['decision_type'],'cultivate_spell')
        ability['parameters']['Reveal']='False'
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        ability['parameters']=copy.deepcopy(CULTIVATE_PARAMETERS);ability['targets']=[dict(player_id=1)]
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
