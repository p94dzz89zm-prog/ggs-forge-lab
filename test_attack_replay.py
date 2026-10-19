import copy
import unittest
from decision_tape import encode, ATTACK

class AttackEncodingTest(unittest.TestCase):
    def test_phoenix_declaration_and_unknown_effect_rejection(self):
        actor=dict(player_id=0,lost=False);before=[actor,dict(attacking_player=actor,attacks=[])]
        attack=dict(attacker=dict(card_id=8,name='Phoenix Chick',controller_id=0,zone='Battlefield',tapped=False,phased_out=False),defender=dict(player_id=1,lost=False),blockers=[],blocked=False)
        after=copy.deepcopy(before);after[1]['attacks']=[attack]
        entry=dict(hook='forge/ai/bridge/PlayerControllerBridge'+ATTACK,call_id=1,receiver=actor,arguments=before,turn=7,phase='COMBAT_DECLARE_ATTACKERS',turn_player_id=0)
        returned=dict(result=None,arguments_after=after)
        self.assertEqual(encode(entry,returned,0,1,2)['attacker_id'],8)
        entry['replay_attack_unknown_calls']=1
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        entry.pop('replay_attack_unknown_calls');attack['defender']['player_id']=0
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')
        attack['defender']['player_id']=1;attack['attacker']['tapped']=True
        self.assertEqual(encode(entry,returned,0,1,2)['kind'],'unsupported_decision')

if __name__=='__main__':unittest.main()
