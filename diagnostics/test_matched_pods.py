import json, tarfile, tempfile, unittest
from pathlib import Path
from analyze_matched_pod_collection import bootstrap_win_difference, metrics, report, unresolved_outcome_bounds
from watch_matched_pod_collection import archive_checkpoint

def row(seed, win, seat=0):
    return {'seed':seed,'ggs_win':win,'ggs_seat':seat,'status':'completed',
        'winner':'Ai(1)-GGS' if win else 'Ai(2)-Jaymie_Ezio','engine_ms':1000,
        'commander_casts':[],'observed_combat_turns':{},'logged_ggs_triggers':0,
        'ninjutsu_paid_return_records':0,'peak_observed_ggs_creatures':0,'last_logged_turn':20}

class MatchedPodTests(unittest.TestCase):
    def test_equal_outcomes_have_zero_interval(self):
        pairs=[(row(s,w),row(s,w)) for s,w in [(1,True),(2,False)]]
        self.assertEqual(bootstrap_win_difference(pairs,100)['approximate_95_percentile_interval'],[0,0])

    def test_rotations_remain_in_seed_clusters(self):
        pairs=[(row(1,True,s),row(1,False,s)) for s in range(4)]
        estimate=bootstrap_win_difference(pairs,100)
        self.assertEqual(estimate['seed_clusters'],1)
        self.assertEqual(estimate['approximate_95_percentile_interval'],[1,1])

    def test_empty_comparison(self):
        self.assertIsNone(bootstrap_win_difference([]))
        self.assertEqual(metrics([]),{'games':0})

    def test_no_casts_are_counted_without_fabricating_timing(self):
        value=metrics([row(1,True),row(2,False)])
        self.assertEqual(value['games_without_logged_commander_cast'],2)
        self.assertIsNone(value['median_first_commander_cast_own_turn'])
        self.assertEqual(value['win_rate'],.5)
        self.assertEqual(value['opponent_wins'],{'Jaymie_Ezio':1})

    def test_unknown_outcomes_are_bounds_not_imputed_results(self):
        value=unresolved_outcome_bounds({'apex':{'games':9,'wins':4},
            'layered':{'games':8,'wins':3}},10)
        self.assertEqual(value['by_deck']['apex']['possible_scheduled_win_rate_range'],[.4,.5])
        self.assertAlmostEqual(value['possible_apex_minus_layered_scheduled_win_rate_range'][0],-.1)
        self.assertAlmostEqual(value['possible_apex_minus_layered_scheduled_win_rate_range'][1],.2)

    def test_report_handles_no_valid_pairs(self):
        self.assertIn('Matched valid pairs: **0**',report({'matched_valid_pairs':0,
            'unresolved_slots':[{}],'matched':{'apex':metrics([]),'layered':metrics([])},
            'all_valid':{'apex':metrics([]),'layered':metrics([])},
            'win_difference':None}))

    def test_checkpoint_keeps_only_checkpointed_attempts(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary);root=base/'run';root.mkdir()
            (root/'protocol.json').write_text('{}')
            folder=root/'apex/rotation0/seed1/attempt1';folder.mkdir(parents=True)
            (folder/'summary.json').write_text('[]')
            (folder/'private-audits.tar.gz').write_bytes(b'compressed-fixture')
            active=root/'layered/rotation0/seed1/attempt1';active.mkdir(parents=True)
            (active/'live.log').write_text('not yet checkpointed')
            records=[{'folder':str(folder.relative_to(root))}]
            archive_checkpoint(root,base/'checkpoint.tar.gz',records)
            with tarfile.open(base/'checkpoint.tar.gz') as archive:
                self.assertEqual(json.load(archive.extractfile('run/attempts.json')),records)
                self.assertFalse(any('layered' in name for name in archive.getnames()))
                self.assertIn('run/apex/rotation0/seed1/attempt1/private-audits.tar.gz',archive.getnames())

if __name__=='__main__':
    unittest.main()
