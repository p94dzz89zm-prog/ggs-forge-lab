import unittest
from reduction_cost_audit import derive

def card(i,types='Creature',mana='{1}',actor=0,phased=False):return dict(id=i,type=types,mana_cost=mana,controller_id=actor,phased_out=phased)

class ReductionTests(unittest.TestCase):
    def test_creatures_across_opponents_include_tokens_not_phased(self):
        r=derive('{8}{R}',[card(1),card(2,actor=1,mana='no cost'),card(3,phased=True),card(4,'Land')],0,'creatures_on_battlefield')
        self.assertEqual(r['reduction'],2);self.assertEqual(r['expected_shards'],{'{1}':6,'{R}':1});self.assertFalse(r['rules_approved'])
    def test_reduction_preserves_colored_requirements_and_floors_generic(self):
        self.assertEqual(derive('{6}{W}{W}',[card(i) for i in range(10)],0,'creatures_on_battlefield')['expected_shards'],{'{W}':2})
    def test_increases_apply_before_reductions(self):
        r=derive('{1}{R}',[card(1),card(2)],0,'creatures_on_battlefield',generic_increase=3)
        self.assertEqual(r['expected_shards'],{'{1}':2,'{R}':1})
    def test_historic_union_counts_each_controlled_permanent_once(self):
        board=[card(1,'Legendary Artifact Creature','{2}{U}'),card(2,'Enchantment - Saga','{1}{W}'),card(3,'Legendary Land','no cost'),card(4,'Artifact','{7}',actor=1),card(5,'Enchantment','{9}')]
        r=derive('{12}',board,0,'controlled_historic_mana_value');self.assertEqual(r['reduction'],5);self.assertEqual(r['expected_shards'],{'{1}':7})
    def test_duplicate_and_missing_characteristics_refuse(self):
        for board in [[card(1),card(1)],[dict(id=1)]]:
            with self.assertRaises(ValueError):derive('{1}',board,0,'creatures_on_battlefield')
    def test_unsupported_cost_or_mechanic_refuses(self):
        for mana in ['{X}','{W/U}','{W/P}','bad']:
            with self.assertRaises(ValueError):derive(mana,[],0,'creatures_on_battlefield')
        with self.assertRaises(ValueError):derive('{1}',[],0,'guess')
    def test_invalid_modifier_not_coerced(self):
        for n in [-1,True,'2']:
            with self.assertRaises(ValueError):derive('{1}',[],0,'creatures_on_battlefield',generic_increase=n)

if __name__=='__main__':unittest.main()
