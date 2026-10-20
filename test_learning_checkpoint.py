import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import adaptive_pilot as pilot
import learning_checkpoint as cp
from learning_gate import FULL_SCOPE

class LearnerCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'model.sqlite'
        self.db=pilot.connect(self.source);self.addCleanup(self.db.close)
    def episode(self, idx=0, mode='train', status='completed', reward=1):
        self.db.execute('INSERT INTO episodes VALUES(?,?,?,?,?,?,?,?,?)',
                        ('private-evidence',idx,'context',mode,100+idx,'ENGINE',status,reward,'{}'))
        self.db.commit()
    def test_committed_wal_survives_snapshot_and_restart(self):
        self.episode();self.assertTrue(self.source.with_name('model.sqlite-wal').exists())
        result=cp.snapshot(self.source,self.root/'frozen.sqlite')
        self.assertEqual(result['readiness']['episodes'],1)
        self.assertFalse(result['readiness']['ready_for_measured_update'])
        self.assertFalse(result['learning_update_performed'])
        self.db.close()
        self.assertEqual(cp.inspect_model(self.root/'frozen.sqlite')['episodes'],1)
        self.assertEqual(hashlib.sha256((self.root/'frozen.sqlite').read_bytes()).hexdigest(), result['model_sha256'])
    def test_pending_rewards_do_not_become_learning(self):
        self.episode()
        r=cp.inspect_model(self.source)
        self.assertEqual(r['revalidated_learning_episodes'],0)
        self.assertEqual(r['episode_admission_counts'],{'not_reviewed':1})
    def test_review_claim_without_evidence_is_rejected(self):
        self.episode()
        self.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?)',('private-evidence',0,'pass',FULL_SCOPE,'fixture only','test'));self.db.commit()
        r=cp.inspect_model(self.source)
        self.assertEqual(r['full_review_claims'],1)
        self.assertEqual(r['revalidated_learning_episodes'],0)
        self.assertTrue(r['evidence_issues'])
    def test_heldout_and_incomplete_excluded_even_with_review_claims(self):
        self.episode(0,mode='evaluate');self.episode(1,status='running',reward=None)
        for idx in (0,1):self.db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?)',('private-evidence',idx,'pass',FULL_SCOPE,'fixture only','test'))
        self.db.commit()
        with patch('review_experience.profile_learning_gate',side_effect=AssertionError('must not admit')):
            r=cp.inspect_model(self.source)
        self.assertEqual(r['revalidated_learning_episodes'],0)
        self.assertEqual(r['episode_admission_counts'],{'evaluation_excluded':1,'incomplete_excluded':1})
    def test_immutable_and_source_preserved(self):
        self.episode();out=self.root/'frozen.sqlite';cp.snapshot(self.source,out);original=out.read_bytes()
        self.episode(1)
        with self.assertRaises(FileExistsError):cp.snapshot(self.source,out)
        self.assertEqual(out.read_bytes(),original)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM episodes').fetchone()[0],2)
    def test_missing_or_wrong_schema_refused(self):
        with self.assertRaises(FileNotFoundError):cp.snapshot(self.root/'missing',self.root/'out')
        bad=self.root/'bad.sqlite';sqlite3.connect(bad).close()
        with self.assertRaises(ValueError):cp.snapshot(bad,self.root/'out')
        self.assertFalse((self.root/'out').exists())
if __name__=='__main__':unittest.main()
