"""Eliminated-player regression plus guards against cross-combat/time leakage."""
import copy,unittest
from analyze import match_life_snapshot

class PhaseReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.s={'global_turn':34,'phase':'COMBAT_END','combat_ordinal':0,'life_vector':{'Pure':3,'Food':10,'Turtles':35}}
  self.q={'line':1015,'combat_ordinal':1,'life':{'Pure':3,'Ezio':0,'Food':10,'Turtles':35},'combat_damage':0,'all_damage':0}
  self.points={(34,'COMBAT_END',1):[self.q]}
 def test_eliminated_active_player_exact_life(self):
  q,ok=match_life_snapshot(self.s,self.points,1005,{34:'Ezio'})
  self.assertTrue(ok);self.assertEqual(q['line'],1015);self.assertEqual(self.s['combat_ordinal'],0)
  self.assertEqual(self.s['canonical_combat_ordinal'],1)
 def test_surviving_active_player_does_not_alias(self):
  self.assertEqual(match_life_snapshot(self.s,self.points,1005,{34:'Food'}),(None,False))
 def test_wrong_life_is_not_accepted(self):
  self.s['life_vector']['Pure']=4
  self.assertEqual(match_life_snapshot(self.s,self.points,1005,{34:'Ezio'}),(None,False))
 def test_cannot_rewind_canonical_order(self):
  self.assertEqual(match_life_snapshot(self.s,self.points,1016,{34:'Ezio'}),(None,False))
 def test_later_extra_combat_cannot_supply_earlier_damage(self):
  self.s['combat_ordinal']=1
  earlier=copy.deepcopy(self.q);earlier['life']['Turtles']=40
  later=copy.deepcopy(self.q);later.update(line=1100,combat_ordinal=2,combat_damage=20,all_damage=20)
  self.points[(34,'COMBAT_END',1)]=[earlier];self.points[(34,'COMBAT_END',2)]=[later]
  q,ok=match_life_snapshot(self.s,self.points,1005,{34:'Ezio'})
  self.assertFalse(ok);self.assertEqual(q['line'],1015);self.assertEqual(q['combat_damage'],0)

if __name__=='__main__':unittest.main()
