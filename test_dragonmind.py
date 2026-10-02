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
        text='\n'.join('DragonMind Result: '+json.dumps({'seed':s,'status':'completed','winner':name}) for s,name in [(4,'A'),(5,'B')])
        rows=parse_results(text,[4,5])
        self.assertEqual(rows[4]['winner'],'A')
        self.assertEqual(rows[5]['winner'],'B')

    def test_duplicate_or_unknown_results_rejected(self):
        row='DragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A'})
        for text,seeds in [(row+'\n'+row,[4]),(row,[5])]:
            with self.assertRaises(ValueError):parse_results(text,seeds)

    def test_missing_results_remain_missing(self):
        self.assertEqual(parse_results('engine crashed before result',[4]),{})

    def test_incomplete_winner_rejected(self):
        row='DragonMind Result: '+json.dumps({'seed':4,'status':'timeout','winner':'A'})
        with self.assertRaises(ValueError):parse_results(row,[4])

    def test_swallowed_ai_exception_invalidates_completion(self):
        row='java.util.concurrent.TimeoutException\nDragonMind Result: '+json.dumps({'seed':4,'status':'completed','winner':'A'})
        self.assertEqual(parse_results(row,[4])[4]['status'],'engine_error')
        self.assertIsNone(parse_results(row,[4])[4]['winner'])

    def test_cancelled_timeout_keeps_timeout_classification(self):
        row='java.lang.InterruptedException\nDragonMind Result: '+json.dumps({'seed':4,'status':'timeout','winner':None})
        self.assertEqual(parse_results(row,[4])[4]['status'],'timeout')


if __name__=='__main__':unittest.main()
