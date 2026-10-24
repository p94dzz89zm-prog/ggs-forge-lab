import copy
import unittest
from decision_tape import encode, SINGLE_PLAYER


class SinglePlayerEncodingTest(unittest.TestCase):
    def test_membership_optional_and_reveal_restrictions(self):
        player=dict(player_id=1,lost=False,life=40)
        ability=dict(source=dict(card_id=5),ability_id=7,api='ChangeZone',parameters={})
        args=[[player],None,ability,'Chooser:',False,None,None]
        entry=dict(hook='forge/ai/PlayerControllerAi'+SINGLE_PLAYER,call_id=1,receiver=dict(player_id=0),arguments=args)
        returned=dict(result=player,arguments_after=copy.deepcopy(args))
        self.assertEqual(encode(entry,returned,0,1,2)['selected_player_id'],1)
        returned['result']=dict(player_id=2)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        returned['result']=None
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        args[4]=True;returned['arguments_after']=copy.deepcopy(args)
        self.assertIsNone(encode(entry,returned,0,1,2)['selected_player_id'])
        args[1]=dict(delayed_reveal=True);returned['arguments_after']=copy.deepcopy(args)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')


if __name__=='__main__':unittest.main()
