import copy
import unittest
from mana_unit_audit import check_pool_transition
import test_referee_tape as fixtures


class ManaPoolAuditTests(unittest.TestCase):
    def setUp(self):
        self.unit = dict(color='U', source_card_id=9, snow=False)

    def test_success_removes_exactly_one_and_preserves_multiplicity(self):
        self.assertIsNone(check_pool_transition([self.unit], [], self.unit))
        self.assertIsNone(check_pool_transition([self.unit, self.unit], [self.unit], self.unit))
        other = dict(self.unit, color='W')
        self.assertIsNone(check_pool_transition([other, self.unit], [other], self.unit))

    def test_fabricated_or_unremoved_or_extra_spending_rejected(self):
        for before, after in (([], []), ([self.unit], [self.unit]),
                              ([self.unit, self.unit], []),
                              ([self.unit], [dict(self.unit, color='W')])):
            with self.subTest(before=before, after=after), self.assertRaises(ValueError):
                check_pool_transition(before, after, self.unit)

    def test_ambiguous_identity_and_snow_rejected(self):
        for field, value in (('source_card_id', True), ('source_card_id', 9.0),
                             ('snow', 'false'), ('snow', 0)):
            unit = dict(self.unit, **{field: value})
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                check_pool_transition([unit], [], unit)

    def test_legacy_snapshots_report_gap(self):
        self.assertEqual(check_pool_transition(None, [], self.unit),
                         'Missing mana pool transition snapshot')
        with self.assertRaises(ValueError):
            check_pool_transition({}, [], self.unit)

    def test_reader_checks_resource_removal_separately_from_cost(self):
        f = fixtures.RefereeTapeTests()
        f.setUp()
        rows = copy.deepcopy(f.rows)
        rows[2]['arguments'][1] = dict(unpaid_shards=['{U}'], generic=0)
        rows[2]['arguments'][2] = self.unit
        rows[2]['mana_context'] = dict(pool=[self.unit], possible_color_uses={'U': 2})
        rows[3]['arguments_after'][1] = dict(unpaid_shards=[], generic=0)
        rows[3]['mana_pool_after'] = []
        result = f.check(rows)
        self.assertEqual(result['mana_pool_transition_checks'], 1)
        self.assertFalse(result['rules_approved'])
        rows[3]['mana_pool_after'] = [self.unit]
        with self.assertRaises(ValueError):
            f.check(rows)
