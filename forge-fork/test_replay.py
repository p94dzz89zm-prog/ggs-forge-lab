import importlib.util,pathlib,unittest
spec=importlib.util.spec_from_file_location('build_replay',pathlib.Path(__file__).with_name('build_replay.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ReplayTests(unittest.TestCase):
    def log(self,winner='B'):
        return ''.join('Game Outcome: '+p+(' has won because all opponents have lost' if p==winner else ' has lost because life total reached 0')+'\n' for p in 'ABCD')+'Game Result: Game 1 ended in 12 ms. '+winner+' has won!\n'
    def test_actual_winner_without_invented_board_or_damage(self):
        frames=[{'players':[{'life':4}],'stack':['old']}]
        final=module.verified_final_frame(frames,self.log())
        self.assertTrue(final['outcome'].startswith('B wins'))
        self.assertEqual(final['action'],'')
        self.assertEqual(frames[0]['stack'],['old'])
        self.assertNotIn('Six permanent Dragons',final['reason'])
    def test_timeout_or_exception_does_not_display_false_win(self):
        for suffix in ('Stopping slow match as draw','java.lang.IllegalStateException'):
            self.assertIsNone(module.verified_final_frame([{}],self.log()+suffix))
    def test_inconsistent_result_rejected(self):
        self.assertIsNone(module.verified_final_frame([{}],self.log().replace('12 ms. B','12 ms. A')))
