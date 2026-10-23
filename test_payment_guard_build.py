import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('payment_guard_build',ROOT/'forge-fork/build_payment_guard.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class PaymentGuardBuildTests(unittest.TestCase):
    def test_wrong_base_refused_without_compiler_or_output(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)/'base.jar';base.write_bytes(b'not the verified executable')
            out=Path(td)/'new.jar'
            with patch('sys.argv',['build','--base',str(base),'--output',str(out)]), patch.object(build.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'Exact verified'):build.main()
                run.assert_not_called();self.assertFalse(out.exists())

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)/'base.jar';base.write_bytes(b'controlled base')
            out=Path(td)/'old.jar';out.write_bytes(b'unique evidence')
            with patch.object(build,'BASE',build.hashlib.sha256(base.read_bytes()).hexdigest()), patch('sys.argv',['build','--base',str(base),'--output',str(out)]), patch.object(build.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'Fresh isolated'):build.main()
                run.assert_not_called();self.assertEqual(out.read_bytes(),b'unique evidence')

    def test_synchronized_workspace_output_refused(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)/'base.jar';base.write_bytes(b'controlled base')
            with patch.object(build,'BASE',build.hashlib.sha256(base.read_bytes()).hexdigest()), patch('sys.argv',['build','--base',str(base),'--output','/workspace/never-created-guard.jar']), patch.object(build.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'Fresh isolated'):build.main()
                run.assert_not_called()

if __name__ == '__main__':unittest.main()
