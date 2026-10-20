import json,tempfile,hashlib,unittest
from pathlib import Path
from evaluation_batch import verify_saved,summary
class BatchEvidenceTests(unittest.TestCase):
 def test_recording_budget_has_bounded_explicit_opt_in(self):
  from unittest.mock import patch
  import evaluation_batch as batch
  common=['evaluation_batch.py','--engine','/tmp/engine','--baseline','/tmp/a.jar','--candidate','/tmp/b.jar','--output','/tmp/new','--source-commit','a'*40,'--seed','123']
  for budget,expected in [('600',0),('601',2),('0',2)]:
   with self.subTest(budget=budget),patch('sys.argv',common+['--timeout',budget]),patch.object(batch,'run',return_value=0) as run:
    with self.assertRaises(SystemExit) as error:batch.main()
    self.assertEqual(error.exception.code,expected)
    self.assertEqual(run.call_count,int(expected==0))
  with patch('sys.argv',common),patch.object(batch,'run',return_value=0) as run:
   with self.assertRaises(SystemExit):batch.main()
   self.assertEqual(run.call_args.args[0].timeout,120)
 def test_changed_evidence_cannot_resume(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);p=root/'game.log';p.write_text('loss');entry={'evidence_sha256':{'game.log':hashlib.sha256(p.read_bytes()).hexdigest()}}
   verify_saved(root,entry);p.write_text('win')
   with self.assertRaises(ValueError):verify_saved(root,entry)
 def test_unknown_or_failed_attempt_is_not_reported_completed(self):
  s=summary({'attempts':[{'label':'candidate','status':'running'}]});self.assertFalse(s['all_completed']);self.assertEqual(s['completed'],0)
 def test_same_seed_build_pair_is_one_cluster(self):
  a={'complete':True,'label':'baseline','game':{'seed':17,'status':'completed'},'learning_gate':{'status':'pending_review'}}
  b={**a,'label':'candidate'};s=summary({'attempts':[a,b]});self.assertEqual(s['independent_seed_clusters'],1);self.assertEqual(s['rules_reviewed_games'],0);self.assertEqual(s['trusted_training_updates'],0)
