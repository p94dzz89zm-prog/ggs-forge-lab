import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import milestone_checkpoint as cp

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'result.log').write_text('done: 3 passed\n')
        self.meta = {'milestone':'persistence-test','source_commit':'a'*40,
                     'attempt_status':'complete', 'trusted_training_updates':0}

    def make(self, **kwargs):
        return cp.create(self.root, self.root/'checkpoint.zip', self.meta,
                         ['result.log'], **kwargs)

    def test_roundtrip_new_session(self):
        receipt = self.make(markers={'result.log':['done: 3 passed']})
        cp.restore(receipt['path'], receipt['sha256'], self.root/'new-session')
        self.assertEqual((self.root/'new-session/result.log').read_bytes(), (self.root/'result.log').read_bytes())
        self.assertIn('Not granted', cp.verify(receipt['path'],receipt['sha256'])['learning_admission'])

    def test_immutable_checkpoint(self):
        receipt = self.make()
        with self.assertRaises(FileExistsError): self.make()
        cp.verify(receipt['path'],receipt['sha256'])

    def test_corruption_rejected(self):
        r = self.make()
        p = Path(r['path']); p.write_bytes(p.read_bytes()[:-20])
        with self.assertRaises(ValueError): cp.verify(p,r['sha256'])

    def test_missing_completion_rejected_before_publish(self):
        with self.assertRaises(ValueError): self.make(markers={'result.log':['missing completion']})
        self.assertFalse((self.root/'checkpoint.zip').exists())

    def test_changed_member_rejected_even_with_new_outer_hash(self):
        r = self.make()
        p = Path(r['path'])
        with zipfile.ZipFile(p) as z: manifest = z.read('MANIFEST.json')
        with zipfile.ZipFile(p,'w') as z:
            z.writestr('MANIFEST.json',manifest); z.writestr('result.log','changed')
        with self.assertRaises(ValueError): cp.verify(p,hashlib.sha256(p.read_bytes()).hexdigest())

    def test_unsafe_paths_and_symlink_rejected(self):
        for name in ('../escape','/absolute','a/../b','a\\b'):
            with self.assertRaises(ValueError): cp.safe_name(name)
        (self.root/'alias').symlink_to(self.root/'result.log')
        with self.assertRaises(ValueError): cp.create(self.root,self.root/'x.zip',self.meta,['alias'])

    def test_restore_preserves_existing_work(self):
        r=self.make(); dest=self.root/'working'; dest.mkdir()
        (dest/'new-work').write_text('keep')
        with self.assertRaises(FileExistsError): cp.restore(r['path'],r['sha256'],dest)
        self.assertEqual((dest/'new-work').read_text(),'keep')

    def test_unknown_attempt_preserved_not_promoted(self):
        self.meta['attempt_status']='unknown_in_flight'
        r=self.make(); m=cp.verify(r['path'],r['sha256'])
        self.assertEqual(m['metadata']['attempt_status'],'unknown_in_flight')
        self.assertEqual(m['metadata']['trusted_training_updates'],0)

if __name__ == '__main__': unittest.main()
