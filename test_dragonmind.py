import json, unittest
from dragonmind import parse_results, java_runtime_flags


class DragonMindResults(unittest.TestCase):
    def test_runtime_flags_record_explicit_compiler_and_collector_choices(self):
        self.assertEqual(java_runtime_flags('parallel','throughput'),['-XX:+UseParallelGC','-XX:-TieredCompilation','-XX:CompileThreshold=1000'])
        self.assertEqual(java_runtime_flags('g1','default'),['-XX:+UseG1GC'])

    def test_timeout_false_winners_cannot_override_structured_failure(self):
        text='Game Outcome: A has won because all opponents have lost\n'
        text+='DragonMind Result: '+json.dumps({'seed':4,'status':'timeout','winner':None,'engine_ms':1000})
        self.assertEqual(parse_results(text,[4])[4]['status'],'timeout')
        self.assertIsNone(parse_results(text,[4])[4]['winner'])

    def test_batch_results_keep_independent_seed_identity(self):
        text='\n'.join('DragonMind Result: '+json.dumps({'seed':s,'status':'completed','winner':name,'engine_ms':1}) for s,name in [(4,'A'),(5,'B')])
        rows=parse_results(text,[4,5])
        self.assertEqual(rows[4]['winner'],'A')
        self.assertEqual(rows[5]['winner'],'B')

    def test_duplicate_or_unknown_results_rejected(self):
        row='DragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A','engine_ms':1})
        for text,seeds in [(row+'\n'+row,[4]),(row,[5])]:
            with self.assertRaises(ValueError):parse_results(text,seeds)

    def test_missing_results_remain_missing(self):
        self.assertEqual(parse_results('engine crashed before result',[4]),{})

    def test_incomplete_winner_rejected(self):
        row='DragonMind Result: '+json.dumps({'seed':4,'status':'timeout','winner':'A','engine_ms':1})
        with self.assertRaises(ValueError):parse_results(row,[4])

    def test_swallowed_ai_exception_invalidates_completion(self):
        row='java.util.concurrent.TimeoutException\nDragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A','engine_ms':1})
        self.assertEqual(parse_results(row,[4])[4]['status'],'engine_error')
        self.assertIsNone(parse_results(row,[4])[4]['winner'])

    def test_cancelled_timeout_keeps_timeout_classification(self):
        row='java.lang.InterruptedException\nDragonMind Result: '+json.dumps({'seed':4,'status':'timeout','winner':None,'engine_ms':1})
        self.assertEqual(parse_results(row,[4])[4]['status'],'timeout')

    def test_final_trailing_exception_invalidates_completion(self):
        row='DragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A','engine_ms':1})
        self.assertEqual(parse_results(row+'\njava.lang.IllegalStateException\n',[4])[4]['status'],'engine_error')

    def test_invalid_duration_rejected(self):
        for duration in (None, -1, True, '1'):
            row='DragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A','engine_ms':duration})
            with self.assertRaises(ValueError):parse_results(row,[4])

    def test_streaming_parser_does_not_require_full_log(self):
        from dragonmind import parse_result_lines
        lines=iter(['arbitrary game detail\n']*10000+['DragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A','engine_ms':1})])
        self.assertEqual(parse_result_lines(lines,[4])[4]['status'],'completed')

    def test_malformed_batch_output_is_recorded_as_failure(self):
        import pathlib, tempfile
        from unittest.mock import patch
        from dragonmind import batch
        def process(*args, **kwargs):
            kwargs['stdout'].write('DragonMind Result: {bad json}\n')
            return type('Process', (), {'returncode':0})()
        with tempfile.TemporaryDirectory() as directory, patch('dragonmind.subprocess.run', side_effect=process):
            rows=batch(pathlib.Path(directory),pathlib.Path('test.jar'),pathlib.Path(directory),'GGS_Layered_v1',0,[4,5],1,False,False)
        self.assertEqual([r['status'] for r in rows],['process_error','process_error'])
        self.assertTrue(all('result_error' in r for r in rows))

    def test_worker_default_respects_resource_limits(self):
        from dragonmind import default_workers
        from unittest.mock import patch
        for cpu,memory,expected in [('800000 100000',str(8*1024**3),2),('200000 100000',str(8*1024**3),1),('800000 100000',str(2*1024**3),1)]:
            with patch('dragonmind.pathlib.Path.read_text',side_effect=[cpu,memory]):
                self.assertEqual(default_workers(),expected)
        with patch('dragonmind.pathlib.Path.read_text',side_effect=OSError):
            self.assertEqual(default_workers(),1)


if __name__=='__main__':unittest.main()
