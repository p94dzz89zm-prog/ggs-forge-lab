import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from executable_delta import create, restore


class ExecutableDeltaTest(unittest.TestCase):
    def test_recovery_rejects_wrong_base_tampered_entry_and_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, target, delta, recovered = [root / name for name in ('base.jar', 'target.jar', 'delta.zip', 'recovered.jar')]
            with zipfile.ZipFile(base, 'w') as archive:
                archive.writestr('policy.class', b'frozen')
                archive.writestr('recorder.class', b'old')
            with zipfile.ZipFile(base) as old, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as new:
                for entry in old.infolist():
                    new.writestr(entry, b'new' if entry.filename == 'recorder.class' else old.read(entry))
                new.writestr('decision_driver.class', b'new driver')
            create(base, target, delta)
            restore(base, delta, recovered)
            self.assertEqual(target.read_bytes(), recovered.read_bytes())
            with self.assertRaises(FileExistsError):
                restore(base, delta, recovered)
            with self.assertRaisesRegex(ValueError, 'Wrong base'):
                restore(target, delta, root / 'wrong.jar')
            corrupt = root / 'corrupt.zip'
            with zipfile.ZipFile(delta) as old, zipfile.ZipFile(corrupt, 'w') as new:
                for entry in old.infolist():
                    new.writestr(entry, b'altered' if entry.filename.startswith('entries/') else old.read(entry))
            with self.assertRaisesRegex(ValueError, 'Changed executable entry'):
                restore(base, corrupt, root / 'corrupt.jar')
            self.assertFalse((root / 'corrupt.jar').exists())
            wrong_result = root / 'wrong-result.zip'
            with zipfile.ZipFile(delta) as old, zipfile.ZipFile(wrong_result, 'w') as new:
                for entry in old.infolist():
                    data = old.read(entry)
                    if entry.filename == 'manifest.json':
                        manifest = json.loads(data)
                        manifest['target_sha256'] = '0' * 64
                        data = json.dumps(manifest).encode()
                    new.writestr(entry, data)
            with self.assertRaisesRegex(ValueError, 'checksum differs'):
                restore(base, wrong_result, root / 'wrong-result.jar')
            self.assertFalse((root / 'wrong-result.jar').exists())


if __name__ == '__main__':
    unittest.main()
