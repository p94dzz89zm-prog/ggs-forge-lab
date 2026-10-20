import json
from pathlib import Path
import sys
import tempfile
import unittest
from natural_game_inputs import fingerprint
from profile_natural_game import run


class ProfiledRunnerTests(unittest.TestCase):
    def prepare(self, code):
        temp=tempfile.TemporaryDirectory(dir='/tmp');self.addCleanup(temp.cleanup)
        root=Path(temp.name);(root/'res').mkdir();(root/'res/card').write_text('synthetic')
        names=['engine','rules','policy_source','legality']+[f'deck{i}' for i in range(4)]
        for name in names:(root/name).write_text('synthetic')
        spec=dict(source_commit='a'*40,seed=12,command=[sys.executable,'-c',code],environment={},
            config=dict(starting_life=40,commander_damage=False,free_seven_mulligans=3,
                format='Commander',seats=['a','b','c','d'],engine_timeout_seconds=1,outer_timeout_seconds=2),
            policies=[dict(architecture='native_baseline',version='synthetic') for _ in range(4)],
            files={name:str(root/name) for name in names}|{'java':str(Path(sys.executable).resolve())},
            resource_root=str(root),deck_legality_evidence='legality')
        (root/'inputs.json').write_text(json.dumps(fingerprint(spec)))
        return root

    def test_process_success_never_approves_game_and_relaunch_is_rejected(self):
        root=self.prepare('print("completed game claim")')
        run(root);result=json.loads((root/'process-final.json').read_text())
        self.assertEqual(result['returncode'],0)
        self.assertFalse(result['rules_approved']);self.assertFalse(result['training_admission'])
        self.assertTrue((root/'inputs-post-run.json').exists())
        with self.assertRaises(FileExistsError):run(root)

    def test_changed_deck_rejected_before_launch(self):
        root=self.prepare('raise AssertionError("must not launch")')
        (root/'deck0').write_text('changed')
        with self.assertRaises(ValueError):run(root)
        self.assertFalse((root/'process.json').exists())

    def test_failed_process_is_retained_with_no_approval(self):
        root=self.prepare('raise SystemExit(7)');run(root)
        result=json.loads((root/'process-final.json').read_text())
        self.assertEqual(result['returncode'],7);self.assertFalse(result['rules_approved'])
        self.assertTrue((root/'console.log').exists())
