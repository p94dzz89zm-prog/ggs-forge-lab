import copy
import unittest
from equipment_attempt_audit import audit,COST

class EquipmentAttemptTests(unittest.TestCase):
    def setUp(self):
        cards=[dict(id=7,name='Equipment',type='Artifact - Equipment',controller_id=0,tapped=False,attachments=[]),dict(id=8,name='Creature',type='Creature - Bear',controller_id=0,tapped=False,attachments=[7]),dict(id=9,name='Land',type='Basic Land',controller_id=0,tapped=False,attachments=[])]
        self.before=dict(state=dict(viewer_id=0,turn=4,phase='MAIN1',active_player_id=0,stack=[],players=[dict(id=0,battlefield=cards)],public_mana_pools=[dict(player_id=0,total=0,units=[])]),decision=dict(selected='7:11'))
        self.after=copy.deepcopy(self.before);self.after['decision']['selected']=None
        ability=dict(ability_id=11,source=dict(card_id=7,name='Equipment'),activating_player_id=0,api='Attach',activated=True,spell=False,direct_targets=[dict(card_id=8)])
        self.rows=[dict(kind='engine_call',hook=COST,call_id=1,turn=4,phase='MAIN1',priority_player_id=0,turn_player_id=0,receiver=dict(base_cost='{2}',ability=ability)),dict(kind='engine_return',hook=COST,call_id=1,result=False)]
    def check(self):return audit(self.rows,self.before,self.after,card_name='Equipment',oracle_equip_cost=2)
    def test_observation_never_establishes_root_cause_or_certifies_game(self):
        r=self.check();self.assertTrue(r['observed_snapshots_unchanged']);self.assertFalse(r['root_cause_established']);self.assertFalse(r['rules_approved']);self.assertFalse(r['training_admission']);self.assertEqual(r['prior_attachment_targets'],[8])
    def test_changed_state_is_explicit(self):
        self.after['state']['players'][0]['battlefield'][2]['tapped']=True
        self.assertFalse(self.check()['observed_snapshots_unchanged'])
    def test_wrong_priority_or_phase_or_nonempty_stack_rejected(self):
        for field,value in [('priority_player_id',1),('turn_player_id',1),('phase','UPKEEP')]:
            old=self.rows[0][field];self.rows[0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check()
            self.rows[0][field]=old
        self.before['state']['stack']=[{}]
        with self.assertRaises(ValueError):self.check()
    def test_wrong_target_controller_or_type_rejected(self):
        c=self.before['state']['players'][0]['battlefield'][1]
        for key,value in [('controller_id',1),('type','Land')]:
            old=c[key];c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check()
            c[key]=old
    def test_fabricated_selection_or_wrong_cost_rejected(self):
        self.before['decision']['selected']='7:12'
        with self.assertRaises(ValueError):self.check()
        self.before['decision']['selected']='7:11';self.rows[0]['receiver']['base_cost']='{1}'
        with self.assertRaises(ValueError):self.check()
    def test_success_and_ambiguous_boolean_not_counted_as_failure(self):
        for value in [True,0,None]:
            self.rows[1]['result']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.check()
    def test_unpaired_or_duplicate_or_missing_payment_rejected(self):
        original=copy.deepcopy(self.rows)
        for rows in [original[:1],original[1:],original[:1]+original,original+original]:
            self.rows=rows
            with self.assertRaises(ValueError):self.check()
    def test_pool_mismatch_and_ambiguous_ids_rejected(self):
        self.before['state']['public_mana_pools'][0]['total']=1
        with self.assertRaises(ValueError):self.check()
        self.before['state']['public_mana_pools'][0]['total']=0;self.rows[0]['receiver']['ability']['ability_id']=True
        with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
