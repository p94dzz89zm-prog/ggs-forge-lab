import json
from pathlib import Path
import tempfile
import unittest
from analyze_jfr_profile import summarize


def sample(names,kind='jdk.ExecutionSample'):
    return dict(type=kind,values=dict(stackTrace=dict(truncated=False,
        frames=[dict(method=dict(type=dict(name=n),name='run')) for n in names])))


class JfrProfileTests(unittest.TestCase):
    def test_recorder_samples_require_actual_frame_and_game_anchor(self):
        events=[sample(['forge/ai/bridge/EngineEvidence','forge/game/phase/PhaseHandler']),
                sample(['forge/game/GameAction','forge/game/phase/PhaseHandler']),
                sample(['forge/ai/bridge/EngineEvidence']),dict(type='jdk.FileWrite',values={})]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'events.json';p.write_text(json.dumps(dict(recording=dict(events=events))))
            r=summarize(p)
        self.assertEqual(r['all_observed_samples'],{'samples':3,'with_recorder_frame':2})
        self.assertEqual(r['phase_handler_anchored_samples'],{'samples':2,'with_recorder_frame':1})
        self.assertFalse(r['rules_approved']);self.assertFalse(r['strategic_improvement_established'])
