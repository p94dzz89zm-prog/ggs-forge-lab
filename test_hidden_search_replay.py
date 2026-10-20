import copy
import unittest
from decision_tape import encode, ZONE_EMPTY

class HiddenSearchEncodingTest(unittest.TestCase):
    def test_empty_search_owner_and_mutation_guards(self):
        params=dict(DB='ChangeZone',Origin='Library',Destination='Hand',Chooser='Targeted',Optional='True',ChangeType='Card.namedSam; Loyal Attendant',ValidTgts='Player',Hidden='True')
        ability=dict(source=dict(card_id=5,name='Frodo, Adventurous Hobbit'),ability_id=7,api='ChangeZone',parameters=params)
        reveal=dict(cards=[dict(view_id=10,zone='Library',owner=dict(view_id=0))],zones=['Library'],owner=dict(view_id=0),message='Looking')
        args=['Hand',['Library'],ability,[],reveal,'Search',True,dict(player_id=0,lost=False)]
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+ZONE_EMPTY,call_id=1,receiver=dict(player_id=0),arguments=args)
        returned=dict(result=None,arguments_after=copy.deepcopy(args))
        self.assertEqual(encode(entry,returned,0,1,2)['reveal_card_ids'],[10])
        ability['source']['name']='Sam, Loyal Attendant'
        params['ChangeType']='Card.namedFrodo; Adventurous Hobbit'
        returned['arguments_after']=copy.deepcopy(args)
        self.assertEqual(encode(entry,returned,0,1,2)['reveal_card_ids'],[10])
        params['ChangeType']='Card.namedSam; Loyal Attendant'
        returned['arguments_after']=copy.deepcopy(args)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        params['ChangeType']='Card.namedFrodo; Adventurous Hobbit'
        returned['arguments_after']=copy.deepcopy(args)
        entry['replay_hidden_random_requests']=1
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        entry.pop('replay_hidden_random_requests');reveal['owner']['view_id']=1;returned['arguments_after']=copy.deepcopy(args)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        reveal['owner']['view_id']=0;returned['arguments_after']=copy.deepcopy(args);returned['result']={'card_id':10}
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
