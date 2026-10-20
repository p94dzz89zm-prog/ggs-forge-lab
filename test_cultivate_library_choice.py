import copy,unittest
from decision_tape import encode,ZONE_EMPTY,CULTIVATE_PARAMETERS

class LibraryChoiceEncodingTest(unittest.TestCase):
    def test_choice_inventory_reorder_allowed_but_membership_and_reveal_guarded(self):
        cards=[dict(card_id=i,name=name,zone='Library',owner_id=0) for i,name in [(10,'Forest'),(20,'Plains')]]
        ability=dict(source=dict(card_id=5,name='Cultivate'),ability_id=7,api='ChangeZone',parameters=CULTIVATE_PARAMETERS)
        reveal=dict(cards=[dict(view_id=card['card_id'],zone='Library',owner=dict(view_id=0)) for card in cards],owner=dict(view_id=0),zones=['Library'],message='Cultivate - Looking at cards in ')
        args=['Library',['Library'],ability,cards,reveal,'Select a card from your library (1 / 2)',True,dict(player_id=0,lost=False)]
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+ZONE_EMPTY,call_id=1,receiver=dict(player_id=0),arguments=args)
        after=copy.deepcopy(args);after[3].reverse();returned=dict(arguments_after=after,result=cards[0])
        self.assertEqual(encode(entry,returned,0,1,2)['available_card_ids'],[10,20])
        returned['result']=dict(card_id=999)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        returned['result']=cards[0];entry['replay_search_effect_calls']=1
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
