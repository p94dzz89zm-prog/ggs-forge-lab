import json
from pathlib import Path
import tempfile
import unittest
from natural_game_diagnostic import summarize


class NaturalDiagnosticTests(unittest.TestCase):
    def run_rows(self, kinds):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'readiness.jsonl'
            rows = [dict(format=1, audience='offline_referee_only', sequence=i,
                         kind=kind, turn=turn, phase='MAIN1', priority=0,
                         players=[dict(id=0, life=40, active=True, library_count=90, battlefield=[])], stack=[])
                    for i, (kind, turn) in enumerate(kinds, 1)]
            path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            return summarize(path)

    def test_partial_progress_never_approves_game(self):
        r = self.run_rows([('trace_begin', 0), ('priority_offer', 1), ('priority_offer', 2)])
        self.assertEqual(r['turns_with_offers'], 2)
        self.assertEqual(r['max_exact_partial_state_repetition'], 1)
        self.assertFalse(r['complete_game_approved'])

    def test_repeated_state_is_reported_not_labeled_rules_defect(self):
        r = self.run_rows([('trace_begin', 0)] + [('priority_offer', 1)]*10)
        self.assertEqual(r['max_exact_partial_state_repetition'], 10)
        self.assertFalse(r['rules_approved'])

    def test_trace_completion_not_terminal_approval(self):
        r = self.run_rows([('trace_begin', 0), ('priority_offer', 1), ('trace_complete', 1)])
        self.assertFalse(r['complete_game_approved'])

    def test_bad_order_and_post_completion_rejected(self):
        for kinds in ([('priority_offer', 1)], [('trace_begin',0),('priority_offer',2),('priority_offer',1)],
                      [('trace_begin',0),('trace_complete',0),('priority_offer',1)]):
            with self.assertRaises(ValueError):self.run_rows(kinds)
