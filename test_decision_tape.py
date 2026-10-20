import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from decision_tape import CARDS, NUMBER, encode, extract

OWNER = 'forge/ai/PlayerControllerAi'


def call(identifier, parent, hook, args):
    return {'kind': 'engine_call', 'call_id': identifier, 'parent_call_id': parent,
            'hook': OWNER + hook, 'arguments': args, 'receiver': {'player_id': 1}, 'speculative': False}


def returned(entry, result):
    return {'kind': 'engine_return', 'call_id': entry['call_id'], 'hook': entry['hook'],
            'arguments_after': copy.deepcopy(entry['arguments']), 'result': result}


class DecisionTapeTest(unittest.TestCase):
    def run_extract(self, rows, *, wrong_hash=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / 'source.jsonl'; output = root / 'decisions.jsonl'
            source.write_text(''.join(json.dumps(dict(format=1, audience='offline_referee_only', **r)) + '\n' for r in rows))
            sha = '0' * 64 if wrong_hash else hashlib.sha256(source.read_bytes()).hexdigest()
            try:
                report = extract(source, sha, output)
                with self.assertRaises(FileExistsError):
                    extract(source, sha, output)
                return report, [json.loads(s) for s in output.read_text().splitlines()]
            except ValueError:
                self.assertFalse(output.exists())
                raise

    def test_root_order_includes_unsupported_parent_without_duplicating_nested_choice(self):
        a = call(1, 0, '.chooseSpellAbilityToPlay()Ljava/util/List;', []); a['initial_state'] = {'players': []}
        nested = call(2, 1, NUMBER, [None, 'number', 1, 5])
        b = call(3, 0, NUMBER, [None, 'number', 1, 5])
        rows = [a, nested, returned(nested, 3), returned(a, []), b, returned(b, 4), {'kind': 'engine_tape_complete', 'calls': 3}]
        report, decisions = self.run_extract(rows)
        self.assertEqual(report['root_decisions'], 2)
        self.assertEqual([r['kind'] for r in decisions], ['unsupported_decision', 'decision', 'decision_tape_complete'])
        self.assertEqual(decisions[1]['number'], 4)
        self.assertEqual(decisions[-1]['unsupported_decisions'], 1)

    def test_mutations_and_fractional_numbers_are_explicitly_unsupported(self):
        entry = call(1, 0, NUMBER, [None, 'number', 1, 5])
        result = returned(entry, 2); result['arguments_after'][1] = 'changed'
        self.assertIn('mutation', encode(entry, result, 0, 1, 2)['reason'])
        self.assertEqual(encode(entry, returned(entry, 2.5), 0, 1, 2)['kind'], 'unsupported_decision')

    def test_card_selection_keeps_exact_live_inventory_and_rejects_missing_identity(self):
        entry = call(1, 0, CARDS, [[{'card_id': 10}, {'card_id': 20}], None, 'cards', 1, 1, False, {}])
        good = encode(entry, returned(entry, [{'card_id': 20}]), 0, 1, 2)
        self.assertEqual(good['available_card_ids'], [10, 20])
        self.assertEqual(good['selected_card_ids'], [20])
        self.assertEqual(encode(entry, returned(entry, [{'card_id': 30}]), 0, 1, 2)['kind'], 'unsupported_decision')

    def test_checksum_or_missing_completion_never_publishes(self):
        entry = call(1, 0, NUMBER, [None, 'number', 1, 5]); entry['initial_state'] = {}
        rows = [entry, returned(entry, 2), {'kind': 'engine_tape_complete', 'calls': 1}]
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.run_extract(rows, wrong_hash=True)
        with self.assertRaisesRegex(ValueError, 'completion'):
            self.run_extract(rows[:-1])

    def test_unpaired_returns_rejected(self):
        entry = call(1, 0, NUMBER, [None, 'number', 1, 5]); entry['initial_state'] = {}
        bad = returned(entry, 2); bad['call_id'] = 2
        with self.assertRaisesRegex(ValueError, 'Unpaired'):
            self.run_extract([entry, bad])


if __name__ == '__main__':
    unittest.main()
