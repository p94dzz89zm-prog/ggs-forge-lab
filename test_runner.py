import unittest
from run_games import classify,validate_deck,ROOT
class RunnerTests(unittest.TestCase):
    def test_timeout_false_winner_rejected(self):
        text='Stopping slow match as draw\nGame Outcome: A has won because all opponents have lost\nGame Result: Game 1 ended in 120000 ms. A has won!'
        self.assertEqual(classify(text)['status'],'timeout')
        self.assertIsNone(classify(text)['winner'])
    def test_crash_false_winner_rejected(self):
        self.assertEqual(classify('java.lang.IllegalStateException\n')['status'],'engine_error')
    def test_ai_evaluation_exception_rejected(self):
        text="java.util.concurrent.TimeoutException\nGame Outcome: A has won because x\nGame Result: Game 1 ended in 12 ms. A has won!"
        self.assertEqual(classify(text)["status"],"engine_error")
    def test_real_completion(self):
        text='Turn: Turn 24 (A)\nGame Outcome: A has won because all opponents have lost\nGame Outcome: B has lost because life total reached 0\nGame Outcome: C has lost because life total reached 0\nGame Outcome: D has lost because life total reached 0\nGame Result: Game 1 ended in 22369 ms. A has won!'
        self.assertEqual(classify(text)['winner'],'A')
    def test_three_player_output_rejected(self):
        text="Game Outcome: A has won because x\nGame Outcome: B has lost because x\nGame Outcome: C has lost because x\nGame Result: Game 1 ended in 2 ms. A has won!"
        self.assertEqual(classify(text)["status"],"unresolved")
    def test_actual_draw_distinguished_from_timeout(self):
        text="".join(f"Game Outcome: {x} has lost because life total reached 0\n" for x in "ABCD")+"Game Result: Game 1 ended in a Draw! Took 20 ms."
        self.assertEqual(classify(text)["status"],"completed_draw")
    def test_multiple_winners_rejected(self):
        self.assertEqual(classify('Game Outcome: A has won because x\nGame Outcome: B has won because x')['status'],'unresolved')
    def test_all_deck_sizes(self):
        for path in (ROOT/'decks').glob('*.dck'): validate_deck(path)
if __name__=='__main__': unittest.main()
