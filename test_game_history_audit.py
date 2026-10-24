import copy
import unittest
from game_history_audit import audit_rows, EXECUTE


def event(kind,**fields):
    return dict(kind='engine_call',hook='forge/game/Game.fireEvent(x)',arguments=[dict(record_type=kind,**fields)])


class GameHistoryTests(unittest.TestCase):
    def setUp(self):
        self.initial=[dict(id=i,life=40) for i in range(4)]
        self.final=[dict(id=i,life=40 if i==0 else 0,active=i==0,won=i==0,lost=i!=0,loss_reason='null' if i==0 else 'LifeReachedZero') for i in range(4)]
        self.rows=[dict(kind='engine_call',initial_state=dict(players=self.initial)),
                   event('GameEventSpellAbilityCast',sa=dict(ability_id=5),si=dict(stack_instance_id=10)),
                   event('GameEventSpellResolved',spell=dict(ability_id=5)),
                   event('GameEventSpellRemovedFromStack',sa=dict(ability_id=5))]
        self.rows += [event('GameEventPlayerLivesChanged',player=dict(view_id=i),oldLives=40,newLives=0) for i in range(1,4)]
        self.rows += [dict(kind='engine_tape_complete',final_state=dict(players=self.final))]

    def test_complete_consistency_never_approves_rules(self):
        r=audit_rows(self.rows);self.assertEqual(r['counts']['lifo_resolution_checks'],1)
        self.assertEqual(r['counts']['last_player_standing_consistency_checks'],1)
        self.assertFalse(r['rules_approved']);self.assertFalse(r['training_admission']);self.assertTrue(r['review_gaps'])

    def test_out_of_order_and_duplicate_resolution_rejected(self):
        rows=copy.deepcopy(self.rows);rows[2]['arguments'][0]['spell']['ability_id']=6
        with self.assertRaises(ValueError):audit_rows(rows)
        with self.assertRaises(ValueError):audit_rows(self.rows[:3]+self.rows[2:])

    def test_broken_life_chain_and_terminal_life_rejected(self):
        rows=copy.deepcopy(self.rows);rows[4]['arguments'][0]['oldLives']=39
        with self.assertRaises(ValueError):audit_rows(rows)
        rows=copy.deepcopy(self.rows);rows[-1]['final_state']['players'][1]['life']=1
        with self.assertRaises(ValueError):audit_rows(rows)

    def test_missing_completion_and_extra_data_rejected(self):
        with self.assertRaises(ValueError):audit_rows(self.rows[:-1])
        with self.assertRaises(ValueError):audit_rows(self.rows+self.rows[:1])
        with self.assertRaises(ValueError):audit_rows(self.rows[:-1]+[dict(kind='engine_tape_complete')])
        rows=copy.deepcopy(self.rows);rows[-1]['final_state']['players'][1]['id']=True
        with self.assertRaises(ValueError):audit_rows(rows)

    def test_refused_actions_distinguish_changes_from_missing_evidence(self):
        entry=dict(kind='engine_call',hook=EXECUTE,call_id=10,execution_state_before={'x':1},execution_mana_before=[])
        result=dict(kind='engine_return',hook=EXECUTE,call_id=10,result=False,execution_state_after={'x':1},execution_mana_after=[])
        r=audit_rows(self.rows[:-1]+[entry,result,self.rows[-1]])
        self.assertEqual(r['counts']['unchanged_refused_action_transitions'],1)
        result['execution_state_after']={'x':2}
        self.assertIn('changed_refused_action_requires_review',audit_rows(self.rows[:-1]+[entry,result,self.rows[-1]])['review_gaps'])
        del result['execution_state_after']
        self.assertIn('missing_refused_action_transition',audit_rows(self.rows[:-1]+[entry,result,self.rows[-1]])['review_gaps'])
