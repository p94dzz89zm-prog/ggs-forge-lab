import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from verify_source_inventory import verify


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'source.py').write_bytes(b'print(1)\n')
        self.manifest = dict(format=2,files={'source.py':dict(sha256=hashlib.sha256(b'print(1)\n').hexdigest())})
        (self.root/'SOURCE_PROVENANCE.json').write_text(json.dumps(self.manifest))
        subprocess.run(['git','add','.'],cwd=self.root,check=True)

    def test_whole_tree_and_hashes_verified_without_game_approval(self):
        result = verify(self.root)
        self.assertEqual(result['verified_files'],2)
        self.assertFalse(result['complete_game_rules_approved'])
        (self.root/'source.py').write_bytes(b'print(2)\n')
        with self.assertRaises(ValueError):verify(self.root)

    def test_sparse_and_extra_trees_are_rejected(self):
        subprocess.run(['git','rm','--cached','source.py'],cwd=self.root,check=True,stdout=subprocess.DEVNULL)
        with self.assertRaises(ValueError):verify(self.root)
        subprocess.run(['git','add','source.py'],cwd=self.root,check=True)
        (self.root/'extra.py').write_bytes(b'print(3)\n')
        subprocess.run(['git','add','extra.py'],cwd=self.root,check=True)
        with self.assertRaises(ValueError):verify(self.root)
