import copy
import unittest
from payment_transaction_audit import audit_rows,PLAN,UNIT,EXECUTE

class PaymentTransactionTests(unittest.TestCase):
    def setUp(self):
        self.ability=dict(ability_id=4,source=dict(card_id=7,name='Probe',mana_cost='{U}'),activating_player_id=0,spell=True,alternative_costs=[],optional_costs=[])
        self.unit=dict(color='U',source_card_id=9,snow=False)
        self.before=dict(cost='{U}',generic=0,remaining_mana_value=1,unpaid_shards=['{U}'])
        self.after=dict(cost='0',generic=0,remaining_mana_value=0,unpaid_shards=[])
        planargs=[self.before,self.ability,dict(player_id=0),False,True,False]
        unitargs=[self.ability,self.before,self.unit,False]
        self.rows=[dict(kind='engine_call',hook=PLAN,call_id=1,parent_call_id=0,speculative=False,arguments=planargs),
            dict(kind='engine_call',hook=UNIT,call_id=2,parent_call_id=1,speculative=False,arguments=unitargs,mana_context=dict(pool=[self.unit],possible_color_uses={'U':2})),
            dict(kind='engine_return',hook=UNIT,call_id=2,result=True,arguments_after=[self.ability,self.after,self.unit,False],mana_pool_after=[]),
            dict(kind='engine_return',hook=PLAN,call_id=1,result=[],arguments_after=[self.after,*planargs[1:]]),
            dict(kind='engine_tape_complete')]
    def check(self,rows=None):return audit_rows(self.rows if rows is None else rows)
    def test_complete_progress_is_scoped_and_never_game_approval(self):
        r=self.check();self.assertEqual(r['counts']['complete_unit_progress_chains'],1);self.assertEqual(r['counts']['printed_to_locked_equal'],1);self.assertFalse(r['rules_approved']);self.assertFalse(r['training_admission']);self.assertEqual(r['gaps'],{})
    def test_success_with_unpaid_cost_rejected(self):
        self.rows[3]['arguments_after'][0]=self.before
        with self.assertRaisesRegex(ValueError,'unpaid'):self.check()
    def test_missing_payment_event_is_explicit_gap(self):
        r=self.check([self.rows[0],self.rows[3],self.rows[4]])
        self.assertEqual(r['gaps']['unobserved_cost_progress_at_return'],1);self.assertNotIn('complete_unit_progress_chains',r['counts'])
    def test_another_ability_or_payer_cannot_receive_credit(self):
        a=copy.deepcopy(self.ability);a['ability_id']=5;self.rows[1]['arguments'][0]=a
        with self.assertRaisesRegex(ValueError,'another ability'):self.check()
    def test_wrong_plan_payer_and_boolean_identity_rejected(self):
        self.rows[0]['arguments'][2]['player_id']=1
        with self.assertRaises(ValueError):self.check()
        self.rows[0]['arguments'][2]['player_id']=0;self.ability['ability_id']=True
        with self.assertRaises(ValueError):self.check()
    def test_pool_or_color_corruption_rejected(self):
        self.rows[2]['mana_pool_after']=[self.unit]
        with self.assertRaisesRegex(ValueError,'exactly one'):self.check()
        self.rows[2]['mana_pool_after']=[];self.unit['color']='R';self.rows[1]['mana_context']['possible_color_uses']={'R':8}
        with self.assertRaises(ValueError):self.check()
    def test_failed_plan_requires_review_without_success_credit(self):
        self.rows[3]['result']=None
        r=self.check();self.assertEqual(r['counts']['failed_mana_plans_requires_rollback_review'],1);self.assertNotIn('complete_unit_progress_chains',r['counts'])
    def test_zero_cost_plan_needs_no_fabricated_unit(self):
        self.rows[0]['arguments'][0]=self.after
        r=self.check([self.rows[0],self.rows[3],self.rows[4]])
        self.assertEqual(r['counts']['complete_unit_progress_chains'],1);self.assertEqual(r['transactions'][0]['units'],0)
    def test_speculative_units_do_not_prove_actual_payment(self):
        self.rows[1]['speculative']=True
        r=self.check();self.assertEqual(r['gaps']['unobserved_cost_progress_at_return'],1);self.assertNotIn('attributed_successful_mana_units',r['counts'])
    def test_unstructured_legacy_cost_is_gap(self):
        self.rows[0]['arguments'][0]='{U}'
        r=self.check();self.assertIn('unstructured_initial_cost',r['gaps']);self.assertNotIn('complete_unit_progress_chains',r['counts'])
    def test_incomplete_reordered_duplicate_and_extra_data_rejected(self):
        for rows in [self.rows[:-1],self.rows[:2]+[self.rows[3],self.rows[2],self.rows[4]],self.rows[:2]+self.rows[1:],self.rows+self.rows[:1]]:
            with self.subTest(rows=len(rows)),self.assertRaises(ValueError):self.check(rows)
    def test_successful_selected_action_requires_observed_priority(self):
        rows=[dict(kind='engine_call',hook=EXECUTE,call_id=1,parent_call_id=0,actor_id=0,priority_player_id=1),dict(kind='engine_return',hook=EXECUTE,call_id=1,result=True),dict(kind='engine_tape_complete')]
        with self.assertRaisesRegex(ValueError,'priority'):self.check(rows)
        rows[1]['result']=False;self.assertFalse(self.check(rows)['rules_approved'])
    def test_missing_or_nonboolean_speculative_flags_rejected(self):
        for index in [0,1]:
            for value in [None,0,'false']:
                old=self.rows[index]['speculative'];self.rows[index]['speculative']=value
                with self.subTest(index=index,value=value),self.assertRaises(ValueError):self.check()
                self.rows[index]['speculative']=old
    def test_return_cannot_change_payment_recipient(self):
        other=copy.deepcopy(self.ability);other['activating_player_id']=1
        self.rows[2]['arguments_after'][0]=other
        with self.assertRaisesRegex(ValueError,'return changed'):self.check()

if __name__=='__main__':unittest.main()
