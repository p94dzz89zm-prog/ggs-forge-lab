import copy
import unittest
from commander_cast_audit import audit_rows
from payment_transaction_audit import EXECUTE, PLAN

EVENT='forge/game/Game.fireEvent(Lforge/game/event/Event;)V'

class CommanderCastTests(unittest.TestCase):
    def setUp(self):
        self.rows=[];self.cid=0
        self.card=dict(card_id=7,name='Commander',owner_id=0,commander=True,zone='Command',mana_cost='{U}')
        self.emit(EVENT,[dict(record_type='GameEventGameStarted')],initial_state=dict(players=[dict(id=0,Command=[self.card],commander_casts={'7':12345})]))
        self.close(EVENT)
    def emit(self,hook,args,parent=0,**kw):
        self.cid+=1;self.rows.append(dict(kind='engine_call',call_id=self.cid,parent_call_id=parent,hook=hook,arguments=copy.deepcopy(args),speculative=False,**kw));return self.cid
    def close(self,hook,cid=None,**kw):self.rows.append(dict(kind='engine_return',hook=hook,call_id=cid or self.cid,**kw))
    def cast(self,origin='Command',generic=0,card=7,actor=0,alternative=None):
        a=dict(ability_id=100+self.cid,source={**self.card,'card_id':card,'zone':origin},activating_player_id=actor,spell=True,alternative_costs=alternative or [],optional_costs=[])
        root=self.emit(EXECUTE,[a],execution_state_before=dict(players=[dict(id=0,**{origin:[dict(card_id=card)]})]));p=self.emit(PLAN,[dict(generic=generic,unpaid_shards=['{1}']*generic+['{U}']),a,dict(player_id=actor),False,True,False],root)
        self.close(PLAN,p,result=[])
        event=self.emit(EVENT,[dict(record_type='GameEventSpellAbilityCast')],root,announced_ability={**a,'source':{**a['source'],'zone':'Stack'}})
        self.close(EVENT,event);self.close(EXECUTE,root,result=True)
    def check(self):return audit_rows(self.rows+[dict(kind='engine_tape_complete')])
    def test_tax_derived_from_cast_events_ignores_cached_counts(self):
        self.cast();self.cast(generic=2);self.cast(generic=4)
        r=self.check();self.assertEqual([e['commander_tax_generic'] for e in r['casts']],[0,2,4]);self.assertEqual(r['counts']['base_plus_tax_equal'],3);self.assertEqual(r['gaps'],{});self.assertFalse(r['complete_game_approved']);self.assertFalse(r['training_admission'])
    def test_hand_cast_neither_pays_nor_increments_tax(self):
        self.cast();self.cast('Hand');self.cast(generic=2)
        self.assertEqual([e['commander_tax_generic'] for e in self.check()['casts']],[0,0,2])
    def test_partner_commanders_count_separately(self):
        self.rows[0]['initial_state']['players'][0]['Command'].append({**self.card,'card_id':8})
        self.cast();self.cast(card=8);self.cast(generic=2)
        self.assertEqual([e['prior_command_casts'] for e in self.check()['casts']],[0,0,1])
    def test_other_player_hand_cast_does_not_share_owner_count(self):
        self.cast();self.cast('Hand',actor=1);self.cast(generic=2)
        self.assertEqual([e['prior_command_casts'] for e in self.check()['casts']],[0,0,1])
    def test_incorrect_locked_tax_is_review_gap(self):
        self.cast();self.cast(generic=0)
        r=self.check();self.assertEqual(r['gaps']['other_modifiers_or_discrepancy'],1);self.assertFalse(r['rules_approved'])
    def test_alternative_cost_not_falsely_certified(self):
        self.cast(alternative=['Free'])
        r=self.check();self.assertEqual(r['gaps']['unsupported_or_ambiguous_cost'],1)
    def test_unknown_origin_rejected(self):
        self.cast(origin='Unknown')
        with self.assertRaisesRegex(ValueError,'origin'):self.check()
    def test_origin_must_match_one_recorded_zone(self):
        self.cast()
        ex=next(r for r in self.rows if r.get('hook')==EXECUTE and r['kind']=='engine_call')
        ex['arguments'][0]['source']['zone']='Hand'
        with self.assertRaisesRegex(ValueError,'pre-execution zone'):self.check()
        ex['arguments'][0]['source']['zone']='Command';ex['execution_state_before']['players'][0]['Hand']=[dict(card_id=7)]
        with self.assertRaisesRegex(ValueError,'pre-execution zone'):self.check()
    def test_identity_or_nonowner_command_cast_rejected(self):
        for kw in [dict(card=8),dict(actor=1)]:
            with self.subTest(kw=kw):
                self.setUp();self.cast(**kw)
                with self.assertRaises(ValueError):self.check()
    def test_missing_initial_and_incomplete_or_extra_data_rejected(self):
        self.cast()
        for rows in [self.rows[2:]+[dict(kind='engine_tape_complete')],self.rows,self.rows+[dict(kind='engine_tape_complete')]+self.rows]:
            with self.subTest(length=len(rows)),self.assertRaises(ValueError):audit_rows(rows)
    def test_failed_execution_after_announcement_rejected(self):
        self.cast();self.rows[-1]['result']=False
        with self.assertRaisesRegex(ValueError,'unsuccessful'):self.check()
    def test_duplicate_announcement_and_changed_ability_rejected(self):
        self.cast();i=next(i for i,r in enumerate(self.rows) if r.get('announced_ability'))
        a=self.rows[i]['announced_ability'];a['ability_id']+=1
        with self.assertRaisesRegex(ValueError,'matching origin'):self.check()
        a['ability_id']-=1;pair=copy.deepcopy(self.rows[i:i+2])
        for r in pair:r['call_id']=999
        self.rows[-1:-1]=pair
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.check()

if __name__=='__main__':unittest.main()
