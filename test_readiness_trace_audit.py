import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from readiness_trace_audit import audit, audit_rows


def trace(kinds):
    return [dict(format=1, audience='offline_referee_only', sequence=i,
                 kind=kind, result=result, turn=1, phase='MAIN1', priority=0,
                 players=[], stack=[], snapshot_scope='partial diagnostic')
            for i, (kind, result) in enumerate(kinds, 1)]


class ReadinessTraceAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = trace([('trace_begin', False), ('readiness_enter', False),
                           ('sba_return', True), ('triggers_return', True),
                           ('sba_return', False), ('triggers_return', False),
                           ('readiness_exit', False), ('priority_offer', False),
                           ('trace_complete', False)])

    def test_trigger_addition_repeats_sba_before_priority(self):
        r = audit_rows(iter(self.rows))
        self.assertEqual((r['readiness_windows'], r['sba_returns'], r['priority_offers']), (1, 2, 1))
        self.assertFalse(r['rules_approved'])
        self.assertFalse(r['complete_game'])

    def test_no_priority_before_fixed_point(self):
        for remove in ((4, 5), (2,), (3,)):
            rows = [r for i, r in enumerate(copy.deepcopy(self.rows)) if i not in remove]
            for i, row in enumerate(rows, 1): row['sequence'] = i
            with self.subTest(remove=remove), self.assertRaises(ValueError):audit_rows(rows)

    def test_changed_state_before_priority_rejected(self):
        rows = copy.deepcopy(self.rows);rows[7]['priority'] = 1
        with self.assertRaises(ValueError):audit_rows(rows)

    def test_zero_toughness_only_rejected_at_settled_boundary(self):
        rows = copy.deepcopy(self.rows)
        card = dict(creature=True, phased_out=False, toughness=0, indestructible=True)
        rows[1]['players'] = [dict(battlefield=[card])]
        self.assertTrue(audit_rows(rows)['protocol_verified'])
        rows[6]['players'] = [dict(battlefield=[card])]
        with self.assertRaises(ValueError):audit_rows(rows)

    def test_phased_out_or_noncreature_zero_toughness_not_sba_failure(self):
        for card in (dict(creature=True, phased_out=True, toughness=0),
                     dict(creature=False, phased_out=False, toughness=0)):
            rows = copy.deepcopy(self.rows)
            rows[6]['players'] = rows[7]['players'] = [dict(battlefield=[card])]
            self.assertTrue(audit_rows(rows)['protocol_verified'])

    def test_no_overlapping_or_duplicate_priority(self):
        for index, kind in ((2, 'readiness_enter'), (8, 'priority_offer')):
            rows = copy.deepcopy(self.rows);rows[index]['kind'] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):audit_rows(rows)

    def test_partial_and_post_terminal_streams_rejected(self):
        with self.assertRaises(ValueError):audit_rows(self.rows[:-1])
        with self.assertRaises(ValueError):audit_rows(self.rows + [self.rows[0]])

    def test_explicit_prefix_inspection_cannot_certify_completion(self):
        for rows in (self.rows[:-1], self.rows[:3], self.rows):
            result = audit_rows(rows, require_complete=False)
            self.assertFalse(result['protocol_verified'])
            self.assertTrue(result['prefix_protocol_checked'])
            self.assertFalse(result['rules_approved'])

    def test_typed_sequence_and_result_required(self):
        for field, value in (('sequence', True), ('sequence', 1.0), ('result', 0), ('format', True)):
            rows = copy.deepcopy(self.rows);rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):audit_rows(rows)

    def test_receipt_binds_original_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'trace.jsonl'
            data = ''.join(json.dumps(r)+'\n' for r in self.rows).encode()
            p.write_bytes(data)
            receipt = dict(records=len(self.rows), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            rp = Path(str(p)+'.receipt.json');rp.write_text(json.dumps(receipt))
            self.assertEqual(audit(p)['priority_offers'], 1)
            p.write_bytes(data+b'\n')
            with self.assertRaises((ValueError, json.JSONDecodeError)):audit(p)
            p.write_bytes(data);receipt['bytes'] = float(len(data));rp.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):audit(p)
