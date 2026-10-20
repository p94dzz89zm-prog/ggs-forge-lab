"""Adversarial evidence types must not impersonate engine identities."""
import copy
import unittest
import test_referee_tape as fixtures


class RefereeTapeTypeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.RefereeTapeTests()
        self.fixture.setUp()

    def test_numeric_aliases_rejected(self):
        for index, field, values in (
            (0, 'format', (True, 1.0, '1')),
            (0, 'call_id', (True, 1.0, '1')),
            (0, 'parent_call_id', (False, 0.0, '0')),
            (1, 'call_id', (True, 1.0, '1')),
            (4, 'calls', (2.0, '2', True)),
        ):
            for value in values:
                with self.subTest(index=index, field=field, value=value):
                    rows = copy.deepcopy(self.fixture.rows)
                    rows[index][field] = value
                    with self.assertRaises(ValueError):
                        self.fixture.check(rows)

    def test_ambiguous_payment_speculation_cannot_skip_real_checks(self):
        for value in ('false', 'true', 0, 1, None):
            with self.subTest(value=value):
                rows = copy.deepcopy(self.fixture.rows)
                rows[2]['speculative'] = value
                with self.assertRaises(ValueError):
                    self.fixture.check(rows)

    def test_random_sequence_numeric_aliases_rejected(self):
        for value in (True, 1.0, '1'):
            rows = copy.deepcopy(self.fixture.rows)
            rows.insert(-1, dict(format=1, audience='offline_referee_only',
                                kind='random_bits', bits=1, value=0,
                                random_index=value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.fixture.check(rows)

    def test_player_identity_types_rejected(self):
        for value in (False, 0.0, '0'):
            rows = copy.deepcopy(self.fixture.rows)
            rows[0]['initial_state']['players'][0]['id'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.fixture.check(rows)

    def test_invalid_hook_and_nonobject_record_rejected(self):
        for value in (None, '', 7):
            rows = copy.deepcopy(self.fixture.rows)
            rows[0]['hook'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.fixture.check(rows)
        with self.assertRaises(ValueError):
            self.fixture.check([[]])

    def test_scoped_reader_still_rejects_duplicate_initial_states(self):
        import io
        import json
        from referee_tape import _inspect
        rows = copy.deepcopy(self.fixture.rows)
        rows[2]['initial_state'] = copy.deepcopy(rows[0]['initial_state'])
        payload = ('\n'.join(map(json.dumps, rows)) + '\n').encode()
        with self.assertRaises(ValueError):
            _inspect(io.BytesIO(payload), require_initial=False)
