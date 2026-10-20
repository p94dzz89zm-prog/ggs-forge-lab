import copy
import unittest
from priority_pass_audit import PriorityPassAudit, CHOICE, ANNOUNCE


class PriorityPassAuditTests(unittest.TestCase):
    def audit(self):
        a = PriorityPassAudit()
        a.next_row(dict(initial_state=dict(players=[dict(id=i, active=True) for i in range(4)])))
        return a

    def setUp(self):
        self.entry = dict(hook='forge/ai/PlayerControllerAi' + CHOICE,
                          speculative=False, receiver=dict(player_id=2, lost=False),
                          priority_player_id=2, phase='MAIN1', arguments=[],
                          mana_context=dict(pool=[dict(color='U'), dict(color='U'), dict(color='C')]))
        self.returned = dict(result=None, arguments_after=[])
        self.announcement = dict(kind='engine_call', hook=ANNOUNCE,
                                 public_payload=dict(reason='priority_pass', player_id=2, counts={'U': 2, 'C': 1}),
                                 visibility_operation='public_mana_pool_announcement',
                                 entitled_player_ids=[0, 1, 2, 3])

    def test_exact_public_counts_and_duplicate_units(self):
        a = self.audit()
        a.returned(self.entry, self.returned)
        a.next_row(self.announcement)
        self.assertEqual(a.report()['priority_mana_disclosure_checks'], 1)
        self.assertFalse(a.report()['priority_derivation_approved'])

    def test_missing_legacy_disclosure_is_gap(self):
        a = PriorityPassAudit()
        a.returned(self.entry, self.returned)
        a.next_row(dict(kind='engine_call', hook='other'))
        self.assertEqual(sum(a.report()['priority_pass_gaps'].values()), 1)
        self.assertEqual(a.report()['priority_mana_disclosure_checks'], 0)

    def test_wrong_player_count_reason_or_audience_rejected(self):
        for field, value in (('player_id', 1), ('player_id', True),
                             ('counts', {'U': 1, 'C': 1}), ('counts', {'U': True, 'C': 1}),
                             ('reason', 'after_cost_payment')):
            with self.subTest(field=field, value=value):
                a = PriorityPassAudit();a.returned(self.entry, self.returned)
                row = copy.deepcopy(self.announcement);row['public_payload'][field] = value
                with self.assertRaises(ValueError):a.next_row(row)
        for audience in ([0, 1], [0, 1, 2, 2], [True, 2]):
            a = PriorityPassAudit();a.returned(self.entry, self.returned)
            row = dict(self.announcement, entitled_player_ids=audience)
            with self.assertRaises(ValueError):a.next_row(row)

    def test_wrong_priority_holder_or_eliminated_actor_rejected(self):
        for entry in (dict(self.entry, priority_player_id=1),
                      dict(self.entry, receiver=dict(player_id=2, lost=True)),
                      dict(self.entry, phase='UNTAP')):
            with self.assertRaises(ValueError):PriorityPassAudit().returned(entry, self.returned)

    def test_cleanup_exception_is_not_blanket_rejected(self):
        a = PriorityPassAudit();a.returned(dict(self.entry, phase='CLEANUP'), self.returned)
        self.assertEqual(a.report()['recorded_priority_entitlement_checks'], 1)
        self.assertFalse(a.report()['priority_derivation_approved'])

    def test_selected_action_speculation_and_nested_queries_are_not_passes(self):
        for entry, returned, nested in ((self.entry, dict(self.returned, result=[{}]), False),
                                        (dict(self.entry, speculative=True), self.returned, False),
                                        (self.entry, self.returned, True)):
            a = PriorityPassAudit();a.returned(entry, returned, nested_priority=nested)
            self.assertEqual(a.report()['priority_passes'], 0)

    def test_empty_pool_needs_no_announcement(self):
        a = PriorityPassAudit()
        a.returned(dict(self.entry, mana_context=dict(pool=[])), self.returned)
        self.assertEqual(a.report()['priority_pass_gaps'], {})

    def test_missing_context_is_explicit_gap(self):
        a = PriorityPassAudit();a.returned(dict(self.entry, mana_context={}), self.returned)
        self.assertEqual(sum(a.report()['priority_pass_gaps'].values()), 1)

    def test_incomplete_public_audience_rejected(self):
        a = self.audit();a.returned(self.entry, self.returned)
        with self.assertRaises(ValueError):
            a.next_row(dict(self.announcement, entitled_player_ids=[2, 3]))

    def test_eliminated_player_removed_from_recorded_audience(self):
        a = self.audit()
        a.next_row(dict(elimination_state_after=dict(players=[dict(id=i, active=i != 1) for i in range(4)])))
        a.returned(self.entry, self.returned)
        a.next_row(dict(self.announcement, entitled_player_ids=[0, 2, 3]))
        self.assertEqual(a.report()['priority_mana_disclosure_checks'], 1)

    def test_unknown_active_audience_does_not_become_disclosure_pass(self):
        a = PriorityPassAudit();a.returned(self.entry, self.returned)
        a.next_row(self.announcement)
        self.assertEqual(a.report()['priority_mana_disclosure_checks'], 0)
        self.assertEqual(sum(a.report()['priority_pass_gaps'].values()), 1)
