import unittest
from compare_batch import wilson,block_sign_p

class ComparisonTests(unittest.TestCase):
    def test_no_games_has_no_interval(self):
        self.assertIsNone(wilson(0,0))
    def test_all_wins_does_not_imply_certain_win_probability(self):
        low,high=wilson(10,10)
        self.assertAlmostEqual(low,0.7224672,places=6)
        self.assertAlmostEqual(high,1)
    def test_one_seed_is_one_block_even_with_multiple_seats(self):
        self.assertEqual(block_sign_p([4]),1)
        self.assertEqual(block_sign_p([1,1,1,1]),0.125)
    def test_balanced_seed_differences_show_no_direction(self):
        self.assertEqual(block_sign_p([2,-2,0]),1)

if __name__=='__main__':unittest.main()
