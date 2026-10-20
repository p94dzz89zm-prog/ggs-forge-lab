import copy,json,tempfile,unittest
from pathlib import Path
from decision_tape import encode,PRIORITY,MISTY_PARAMETERS
from audit_misty_costs import audit

class MistyActivationTest(unittest.TestCase):
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
