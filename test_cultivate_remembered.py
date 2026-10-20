import copy
import unittest
from decision_tape import encode, ZONE_EMPTY, CULTIVATE_BATTLEFIELD, CULTIVATE_HAND

class CultivateRememberedTest(unittest.TestCase):
    def fixture(self,destination):
        parameters=CULTIVATE_BATTLEFIELD if destination=='Battlefield' else CULTIVATE_HAND
        cards=[dict(card_id=i,name='Plains',zone='Library',owner_id=1) for i in (188,189)]
        ability=dict(api='ChangeZone',ability_id=50,source=dict(card_id=106,name='Cultivate',zone='Stack'),parameters=parameters.copy())
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+ZONE_EMPTY,receiver=dict(player_id=1),call_id=1,arguments=[destination,['Library'],ability,cards,None,parameters['SelectPrompt'],False,dict(player_id=1,lost=False)])
        returned=dict(result=cards[1].copy(),arguments_after=copy.deepcopy(entry['arguments']))
        return entry,returned
    def test_native_domain_not_presentation_order(self):
        for destination in ('Battlefield','Hand'):
            a,b=self.fixture(destination);b['arguments_after'][3].reverse()
            row=encode(a,b,431,1,2)
            self.assertEqual(row['decision_type'],'cultivate_remembered_choice')
            self.assertEqual(row['available_card_ids'],[188,189])
            self.assertEqual(row['selected_card_id'],189)
    def test_unknown_effect_domain_owner_choice_and_definition_reject(self):
        for mutation in ('effect','domain','owner','selected','parameters','optional'):
            a,b=self.fixture('Battlefield')
            if mutation=='effect':a['replay_search_effect_calls']=1
            elif mutation=='domain':b['arguments_after'][3].pop()
            elif mutation=='owner':a['arguments'][3][0]['owner_id']=0;b['arguments_after']=copy.deepcopy(a['arguments'])
            elif mutation=='selected':b['result']['card_id']=999
            elif mutation=='parameters':a['arguments'][2]['parameters']['Tapped']='False';b['arguments_after']=copy.deepcopy(a['arguments'])
            else:a['arguments'][6]=True;b['arguments_after']=copy.deepcopy(a['arguments'])
            self.assertEqual(encode(a,b,431,1,2)['kind'],'unsupported_decision',mutation)

if __name__=='__main__':unittest.main()
