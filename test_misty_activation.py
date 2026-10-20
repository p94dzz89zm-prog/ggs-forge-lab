import copy,json,tempfile,unittest
from pathlib import Path
from decision_tape import encode,PRIORITY,ZONE_EMPTY,MISTY_PARAMETERS
from audit_misty_costs import audit

class MistyActivationTest(unittest.TestCase):
    def test_sacrificed_source_search_inventory_and_visibility(self):
        owner=dict(view_id=2)
        ability=dict(api='ChangeZone',ability_id=2059,source=dict(card_id=216,name='Misty Rainforest',zone='Graveyard'),parameters=MISTY_PARAMETERS.copy(),activated=True,spell=False,trigger=False,x=None,targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        offered=[dict(card_id=274,name='Watery Grave',owner_id=2,zone='Library')]
        reveal=dict(cards=[dict(view_id=274,owner=owner,zone='Library')],owner=owner,zones=['Library'],message='Misty Rainforest - Looking at cards in ')
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+ZONE_EMPTY,receiver=dict(player_id=2),call_id=1,arguments=['Battlefield',['Library'],ability,offered,reveal,'Select a card from your library',True,dict(player_id=2,lost=False)])
        result=dict(arguments_after=copy.deepcopy(entry['arguments']),result=offered[0].copy())
        self.assertEqual(encode(entry,result,456,1,2)['decision_type'],'misty_library_choice')
        for mutation in ('effect','owner','choice'):
            a,b=copy.deepcopy(entry),copy.deepcopy(result)
            if mutation=='effect':a['replay_search_effect_calls']=1
            elif mutation=='owner':a['arguments'][4]['owner']['view_id']=0;b['arguments_after']=copy.deepcopy(a['arguments'])
            else:b['result']['card_id']=999
            self.assertEqual(encode(a,b,456,1,2)['kind'],'unsupported_decision')
    def test_exact_activation_only(self):
        ability=dict(api='ChangeZone',ability_id=1225,source=dict(card_id=216,name='Misty Rainforest',zone='Battlefield',owner_id=2,controller_id=2,tapped=False,phased_out=False),parameters=MISTY_PARAMETERS.copy(),activated=True,spell=False,trigger=False,x=None,targets=[],paying_mana=[],alternative_costs=[],optional_costs=[])
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+PRIORITY,receiver=dict(player_id=2),call_id=1,arguments=[],turn=11,phase='MAIN1',priority_player_id=2,turn_player_id=2)
        result=dict(result=[ability],arguments_after=[])
        self.assertEqual(encode(entry,result,450,1,2)['decision_type'],'misty_activation')
        for field in ('tapped','phased_out'):
            bad=copy.deepcopy(result);bad['result'][0]['source'][field]=True
            self.assertEqual(encode(entry,bad,450,1,2)['kind'],'unsupported_decision')
        bad=copy.deepcopy(result);bad['result'][0]['parameters']['Cost']='T'
        self.assertEqual(encode(entry,bad,450,1,2)['kind'],'unsupported_decision')

    def test_missing_payment_and_failed_total_reject(self):
        # This independent audit must reject incomplete or nominal-success-only
        # evidence; a successful total return cannot substitute for paid costs.
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'evidence.jsonl'
            enter=dict(kind='engine_call',call_id=1,turn=11,hook='forge/game/cost/CostPayment.payComputerCosts(X)Z',arguments=[],receiver=dict(base_cost='{T}, Pay 1 life, Sacrifice CARDNAME',ability=dict(source=dict(card_id=216))))
            for success in (False,True):
                end=dict(kind='engine_return',call_id=1,hook=enter['hook'],result=success)
                path.write_text(json.dumps(enter)+'\n'+json.dumps(end)+'\n')
                with self.assertRaises(ValueError):audit(path,216,11)

if __name__=='__main__':unittest.main()
