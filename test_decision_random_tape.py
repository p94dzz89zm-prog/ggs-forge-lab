import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from decision_random_tape import extract


class DecisionRandomTapeTest(unittest.TestCase):
    def test_engine_randomness_preserved_and_only_pure_prefix_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'; decisions = root/'decisions'
            records = [dict(kind='random_bits', random_index=1, bits=31, value=4),
                       dict(kind='engine_call'),
                       dict(kind='random_bits', random_index=2, bits=31, value=5),
                       dict(kind='engine_return'),
                       dict(kind='random_bits', random_index=3, bits=31, value=6),
                       dict(kind='engine_call'),
                       dict(kind='random_bits', random_index=4, bits=31, value=7)]
            source.write_text(''.join(json.dumps(r)+'\n' for r in records))
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            choices = [dict(index=0, kind='decision', decision_type='priority_pass', source_call_record=2, source_return_record=4),
                       dict(index=1, kind='unsupported_decision', source_call_record=6),
                       dict(kind='decision_tape_complete', source_sha256=checksum, decisions=2)]
            decisions.write_text(''.join(json.dumps(r)+'\n' for r in choices))
            report = extract(source, checksum, decisions, root/'rng')
            self.assertEqual(report['engine_random_requests'], 2)
            self.assertEqual(report['skipped_pure_choice_random_requests'], 1)
            values = [json.loads(line).get('value') for line in (root/'rng').read_text().splitlines()]
            self.assertEqual(values, [4, 6, None])
            with self.assertRaises(ValueError):
                extract(source, '0'*64, decisions, root/'wrong')


if __name__ == '__main__':
    unittest.main()
