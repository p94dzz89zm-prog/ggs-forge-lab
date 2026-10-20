import copy
import json
import tempfile
import unittest
from pathlib import Path
from referee_tape import inspect


class RefereeTapeTests(unittest.TestCase):
    def setUp(self):
        initial={'players':[{'id':i,'Library':[],'Hand':[],'Command':[]} for i in range(4)]}
        self.rows=[{'kind':'engine_call','call_id':1,'parent_call_id':0,'hook':'start','initial_state':initial},
                   {'kind':'engine_return','call_id':1,'hook':'start'},
                   {'kind':'engine_call','call_id':2,'parent_call_id':0,'hook':'forge/game/mana/ManaPool.tryPayCostWithMana(x)','arguments':[{},'1',{'source_card_id':7},False],'speculative':False},
                   {'kind':'engine_return','call_id':2,'hook':'forge/game/mana/ManaPool.tryPayCostWithMana(x)','result':True,'arguments_after':[{},'0',{},False]},
                   {'kind':'engine_tape_complete','calls':2}]
        for r in self.rows:r.update(format=1,audience='offline_referee_only')
    def check(self,rows):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'tape.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in rows));return inspect(p)
    def test_payments_are_not_rules_approval(self):
        r=self.check(self.rows);self.assertEqual(r['actual_mana_units_paid'],1);self.assertEqual(r['registered_players'],4);self.assertFalse(r['rules_approved'])
    def test_speculative_and_test_units_do_not_count(self):
        for field in ('speculative','test'):
            rows=copy.deepcopy(self.rows)
            if field=='speculative':rows[2]['speculative']=True
            else:rows[2]['arguments'][3]=True
            self.assertEqual(self.check(rows)['actual_mana_units_paid'],0)
    def test_truncated_and_unpaired_calls_rejected(self):
        for rows in (self.rows[:-1],self.rows[:3]+self.rows[4:],self.rows[:2]+self.rows[3:]):
            with self.assertRaises(ValueError):self.check(rows)
    def test_return_order_and_hook_bound(self):
        rows=copy.deepcopy(self.rows);rows[3]['hook']='changed'
        with self.assertRaises(ValueError):self.check(rows)
    def test_visibility_unknown_recipient_rejected(self):
        rows=copy.deepcopy(self.rows);rows[2].update(visibility_operation='look_specified',entitled_player_ids=[9])
        with self.assertRaises(ValueError):self.check(rows)
    def test_unknown_values_retained_as_gaps(self):
        rows=copy.deepcopy(self.rows);rows[2]['arguments'][0]={'unencoded':'unsupported.Choice'}
        self.assertEqual(self.check(rows)['unencoded_types'],{'unsupported.Choice':1})
    def test_random_range_and_sequence(self):
        row={'format':1,'audience':'offline_referee_only','kind':'random_bits','bits':4,'value':16,'random_index':1};rows=self.rows[:-1]+[row,self.rows[-1]]
        with self.assertRaises(ValueError):self.check(rows)
        row['value']=2;row['random_index']=3
        with self.assertRaises(ValueError):self.check(rows)
    def test_extra_rows_and_initial_gaps_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0].pop('initial_state')
        with self.assertRaises(ValueError):self.check(rows)
        with self.assertRaises(ValueError):self.check(self.rows+self.rows[:1])
