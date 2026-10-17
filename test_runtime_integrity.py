"""Operational regressions for observed truncated/changing engine archives."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('pilot_runtime',Path(__file__).parent/'forge-fork/run_pilot_recovery.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)

class RuntimeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.jar=Path(self.directory.name)/'engine.jar'
        with zipfile.ZipFile(self.jar,'w',zipfile.ZIP_STORED) as z:z.writestr('engine.class',b'original-engine-bytes')
        self.frozen=hashlib.sha256(self.jar.read_bytes()).hexdigest()
    def test_closed_archive_matches_frozen_bytes(self):
        self.assertEqual(runtime.verify_archive(self.jar,self.frozen),self.frozen)
    def test_missing_central_directory_is_rejected(self):
        self.jar.write_bytes(self.jar.read_bytes()[:-22])
        with self.assertRaises(zipfile.BadZipFile):runtime.verify_archive(self.jar)
    def test_crc_corruption_is_rejected_even_with_current_outer_hash(self):
        data=self.jar.read_bytes().replace(b'original-engine-bytes',b'corrupt!-engine-bytes');self.jar.write_bytes(data)
        with self.assertRaisesRegex(ValueError,"CRC"):runtime.verify_archive(self.jar,hashlib.sha256(data).hexdigest())
    def test_valid_replaced_archive_cannot_pass_old_frozen_hash(self):
        with zipfile.ZipFile(self.jar,'w') as z:z.writestr('engine.class',b'another-valid-engine')
        with self.assertRaisesRegex(ValueError,'SHA256'):runtime.verify_archive(self.jar,self.frozen)
