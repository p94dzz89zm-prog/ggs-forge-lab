import tempfile
from pathlib import Path
import unittest
from population_protocol import specification,seat_profiles,POPULATIONS

class PopulationTests(unittest.TestCase):
 def test_personalities_follow_decks_through_all_seats(self):
  expected=['Default','Reckless','Cautious','Default']
  for rotation in range(4):self.assertEqual(seat_profiles(tuple(expected),rotation),expected[rotation:]+expected[:rotation])
 def test_heldout_enemy_personality_excluded_from_training(self):
  self.assertTrue(set(POPULATIONS['unseen_evaluation'][1:]).isdisjoint(POPULATIONS['diverse_training'][1:]))
 def test_profile_path_and_rotation_rejected(self):
  for bad in [('../Default','Default','Default','Default'),('Default',)]:
   with self.assertRaises(ValueError):seat_profiles(bad,0)
  with self.assertRaises(ValueError):seat_profiles(POPULATIONS['stock'],4)
 def test_missing_personality_is_not_silently_defaulted(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):specification(Path(td),'diverse_training')
