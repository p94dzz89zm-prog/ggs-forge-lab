"""Synthetic integrity contracts; none are additional gameplay evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import milestone_checkpoint as checkpoint
import side_capture as s


class SideCaptureTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.side = self.root / 'baseline'
        self.side.mkdir()
        self.file = self.side / 'audit.jsonl'
        self.file.write_text('{"turn":1}\n{"turn":2}\n')
        self.entry = {'label': 'baseline', 'status': 'saved', 'complete': True,
                      'evidence_sha256': {'audit.jsonl': hashlib.sha256(self.file.read_bytes()).hexdigest()}}
        self.protocol = {'format': 3, 'seed': 123, 'purpose': 'heldout'}

    def capture(self):
        self.entry['immutable_capture'] = s.capture(self.root, self.entry, self.protocol, '1' * 40)

    def test_capture_restores_original_bytes_and_retains_hash_binding(self):
        self.capture()
        receipt = self.entry['immutable_capture']
        archive = self.root / receipt['relative_path']
        s.verify_capture(self.root, self.entry, self.protocol)
        dest = self.root / 'restored'
        checkpoint.restore(archive, receipt['sha256'], dest)
        self.assertEqual((dest / 'evidence/audit.jsonl').read_bytes(), self.file.read_bytes())
        self.assertEqual(json.loads((dest / 'finalization.json').read_text()), s.finalized_entry(self.entry))

    def test_reappeared_staging_prefix_rejected_without_touching_sealed_capture(self):
        self.capture()
        ghost=self.file.with_name(self.file.name+'.partial')
        ghost.write_text('{"turn":1}\n')
        s.verify_capture(self.root,self.entry,self.protocol)
        with self.assertRaisesRegex(ValueError,'unbound'):
            s.verify_live(self.side,self.entry)
        self.assertEqual(ghost.read_text(),'{"turn":1}\n')

    def test_parseable_tail_loss_before_capture_rejected(self):
        self.file.write_text('{"turn":1}\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.capture()
        self.assertFalse((self.root / 'captures/baseline.zip').exists())

    def test_changed_live_file_never_repaired_from_intact_capture(self):
        self.capture()
        self.file.write_text('{"turn":1}\n')
        s.verify_capture(self.root, self.entry, self.protocol)
        with self.assertRaises(ValueError):
            s.verify_live(self.side, self.entry)
        self.assertEqual(self.file.read_text(), '{"turn":1}\n')

    def test_changed_capture_rejected_even_if_live_files_are_intact(self):
        self.capture()
        archive = self.root / self.entry['immutable_capture']['relative_path']
        archive.write_bytes(archive.read_bytes()[:-10])
        with self.assertRaises(ValueError):
            s.verify_capture(self.root, self.entry, self.protocol)

    def test_journal_rehash_does_not_bless_original_capture(self):
        self.capture()
        self.entry['evidence_sha256']['audit.jsonl'] = '0' * 64
        with self.assertRaises(ValueError):
            s.verify_capture(self.root, self.entry, self.protocol)

    def test_missing_archive_and_changed_protocol_rejected(self):
        self.capture()
        with self.assertRaises(ValueError):
            s.verify_capture(self.root, self.entry, {**self.protocol, 'seed': 124})
        (self.root / self.entry['immutable_capture']['relative_path']).unlink()
        with self.assertRaises(OSError):
            s.verify_capture(self.root, self.entry, self.protocol)

    def test_existing_archive_never_overwritten_after_interruption(self):
        receipt = s.capture(self.root, self.entry, self.protocol, '1' * 40)
        archive = self.root / receipt['relative_path']
        before = archive.read_bytes()
        with self.assertRaises(FileExistsError):
            self.capture()
        self.assertEqual(before, archive.read_bytes())

    def test_extra_file_or_unsafe_path_cannot_be_captured(self):
        (self.side / 'extra.log').write_text('unbound')
        with self.assertRaises(ValueError):
            self.capture()
        (self.side / 'extra.log').unlink()
        self.entry['evidence_sha256'] = {'../outside.log': '0' * 64}
        with self.assertRaises(ValueError):
            self.capture()

    def test_mutation_during_archive_creation_is_rejected(self):
        original = checkpoint.create
        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            self.file.write_text('{"turn":1}\n')
            return result
        with patch('side_capture.checkpoint.create', mutate):
            with self.assertRaisesRegex(ValueError, 'changed'):
                self.capture()
