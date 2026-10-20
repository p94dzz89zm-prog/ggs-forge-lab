import copy
import unittest
from decision_tape import encode, CONFIRM_ACTION


class ConfirmationEncodingTest(unittest.TestCase):
    def test_boolean_source_prompt_and_no_context_mutation(self):
        ability=dict(source=dict(card_id=5),ability_id=7,api='ChangeZone',parameters={})
        args=[ability,'ChangeZoneGeneral','Search your library?',None]
        entry=dict(hook='forge/game/player/PlayerController'+CONFIRM_ACTION,call_id=1,receiver=dict(player_id=0),arguments=args)
        returned=dict(result=False,arguments_after=copy.deepcopy(args))
        self.assertFalse(encode(entry,returned,0,1,2)['accept'])
        returned['result']=True
        self.assertTrue(encode(entry,returned,0,1,2)['accept'])
        returned['result']=1
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        returned['result']=True;args[3]={'unknown':'context'};returned['arguments_after']=copy.deepcopy(args)
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')


if __name__=='__main__':unittest.main()
