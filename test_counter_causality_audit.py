import copy
import unittest
from counter_causality_audit import audit_rows, EVENT, RESOLVE, COUNTER


def ability(aid, card):
    return dict(ability_id=aid, source=dict(card_id=card), direct_targets=[])


def view(aid, card):
    return dict(ability_id=aid, source=dict(view_id=card, owner=dict(view_id=0)))


def fixture(destination='Graveyard'):
    rows = []

    def enter(cid, hook, parent=0, **extra):
        rows.append(dict(kind='engine_call', call_id=cid, hook=hook, parent_call_id=parent,
                         speculative=False, **extra))

    def leave(cid, hook):
        rows.append(dict(kind='engine_return', call_id=cid, hook=hook, result=None))

    def event(cid, tag, parent=0, **fields):
        enter(cid, EVENT, parent, arguments=[dict(record_type=tag, **fields)])
        leave(cid, EVENT)

    enter(1, 'initial', initial_state=dict(players=[])); leave(1, 'initial')
    event(2, 'GameEventSpellAbilityCast', sa=view(10, 100), si=dict(stack_instance_id=1000))
    event(3, 'GameEventSpellAbilityCast', sa=view(20, 200), si=dict(stack_instance_id=2000))
    counter = ability(20, 200); counter['direct_targets'] = [ability(10, 100)]
    enter(4, RESOLVE, receiver=[dict(ability=counter, stack_instance_id=2000),
                               dict(ability=ability(10, 100), stack_instance_id=1000)])
    enter(5, COUNTER, 4, arguments=[counter])
    event(6, 'GameEventSpellRemovedFromStack', 5, sa=view(10, 100))
    event(7, 'GameEventCardChangeZone', 5, card=dict(view_id=100),
          **{'from':dict(zoneType='Stack'), 'to':dict(zoneType=destination, player=dict(view_id=0))})
    leave(5, COUNTER)
    event(8, 'GameEventSpellResolved', 4, spell=view(20, 200))
    event(9, 'GameEventSpellRemovedFromStack', 4, sa=view(20, 200))
    leave(4, RESOLVE)
    rows.append(dict(kind='engine_tape_complete'))
    for i, row in enumerate(rows):
        row['stream_sequence'] = i + 1
    return rows


def call(rows, cid):
    return next(r for r in rows if r.get('call_id') == cid and r['kind'] == 'engine_call')


class CounterCausalityTests(unittest.TestCase):
    def test_structured_link_never_approves_rules_or_training(self):
        result = audit_rows(fixture())
        self.assertEqual(len(result['causal_links']), 1)
        self.assertEqual(result['causal_links'][0]['counter_ability_id'], 20)
        self.assertEqual(result['causal_links'][0]['zone'], 'Graveyard')
        self.assertFalse(result['review_gaps'])
        self.assertFalse(result['rules_approved'])
        self.assertFalse(result['training_admission'])
        self.assertTrue(result['limitations'])

    def test_counter_target_mismatch_and_self_target_rejected(self):
        for aid in (11, 20):
            rows = fixture(); call(rows, 5)['arguments'][0]['direct_targets'][0]['ability_id'] = aid
            with self.assertRaises(ValueError): audit_rows(rows)

    def test_same_ability_different_card_rejected(self):
        rows = fixture(); call(rows, 5)['arguments'][0]['direct_targets'][0]['source']['card_id'] = 101
        with self.assertRaises(ValueError): audit_rows(rows)

    def test_wrong_resolving_object_and_snapshot_order_rejected(self):
        rows = fixture(); call(rows, 5)['arguments'][0]['ability_id'] = 10
        with self.assertRaises(ValueError): audit_rows(rows)
        rows = fixture(); call(rows, 4)['receiver'].reverse()
        with self.assertRaises(ValueError): audit_rows(rows)

    def test_broken_ancestry_and_speculative_evidence_rejected(self):
        rows = fixture(); call(rows, 6)['parent_call_id'] = 999
        with self.assertRaises(ValueError): audit_rows(rows)
        rows = fixture(); call(rows, 5)['speculative'] = True
        with self.assertRaises(ValueError): audit_rows(rows)

    def test_missing_target_is_explicit_gap(self):
        rows = fixture(); del call(rows, 5)['arguments'][0]['direct_targets']
        result = audit_rows(rows)
        self.assertEqual(result['review_gaps']['counter_direct_targets_missing'], 1)
        self.assertFalse(result['causal_links'])

    def test_missing_departure_does_not_link(self):
        rows = [r for r in fixture() if r.get('call_id') != 7]
        for i, row in enumerate(rows): row['stream_sequence'] = i + 1
        result = audit_rows(rows)
        self.assertEqual(result['review_gaps']['counter_target_departure_missing'], 1)
        self.assertFalse(result['causal_links'])

    def test_owner_graveyard_and_origin_checked(self):
        for field, value in [('player',dict(view_id=1)), ('zoneType','Hand')]:
            rows = fixture(); event = call(rows, 7)['arguments'][0]
            if field == 'player': event['to'][field] = value
            else: event['from'][field] = value
            with self.assertRaises(ValueError): audit_rows(rows)

    def test_replacement_destination_requires_review(self):
        result = audit_rows(fixture('Exile'))
        self.assertEqual(result['review_gaps']['counter_destination_requires_replacement_review'], 1)
        self.assertFalse(result['rules_approved'])

    def test_completion_and_boolean_ids_fail_closed(self):
        rows = fixture()
        with self.assertRaises(ValueError): audit_rows(rows[:-1])
        with self.assertRaises(ValueError): audit_rows(rows + [copy.deepcopy(rows[0])])
        call(rows, 5)['arguments'][0]['ability_id'] = True
        with self.assertRaises(ValueError): audit_rows(rows)

    def test_exception_never_becomes_causal_link(self):
        rows = fixture()
        next(r for r in rows if r.get('call_id') == 5 and r['kind'] == 'engine_return')['error'] = 'failure'
        result = audit_rows(rows)
        self.assertFalse(result['causal_links'])
        self.assertEqual(result['review_gaps']['counter_effect_exception'], 1)

    def test_serialized_throwable_never_becomes_causal_link(self):
        rows = fixture()
        next(r for r in rows if r.get('call_id') == 5 and r['kind'] == 'engine_return')['result'] = {'context_type':'java.lang.IllegalStateException'}
        self.assertFalse(audit_rows(rows)['causal_links'])

    def test_sequence_gap_and_reorder_rejected(self):
        rows = fixture(); rows[4]['stream_sequence'] += 1
        with self.assertRaises(ValueError): audit_rows(rows)

    def test_reused_stack_instance_rejected_after_departure(self):
        rows = fixture()
        # A later new announcement may reuse a card/ability, never an instance.
        extra = copy.deepcopy(call(rows, 3)); extra['call_id'] = 100
        extra['arguments'][0]['sa'] = view(30, 300)
        ret = dict(kind='engine_return',call_id=100,hook=EVENT,result=None)
        rows[-1:-1] = [extra, ret]
        for i, row in enumerate(rows): row['stream_sequence'] = i + 1
        with self.assertRaises(ValueError): audit_rows(rows)
