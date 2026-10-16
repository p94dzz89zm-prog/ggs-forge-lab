import tempfile
import unittest
from pathlib import Path
import adaptive_pilot as a
from review_experience import record_review

class ExperienceTests(unittest.TestCase):
 def test_repetition_changes_preference_and_survives_restart(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/"experience.sqlite";db=a.connect(path)
   for i in range(120):
    profile=a.select_profile(a.statistics(db,"deck"),True)
    # Controlled feedback fixture, not an empirical claim about the profiles.
    reward={"BALANCED":.1,"ENGINE":.8,"ECONOMY":.2}[profile]
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,"deck","train",i,profile,"completed",reward,"{}"));db.commit()
   db.close();db=a.connect(path)
   stats=a.statistics(db,"deck")
   self.assertEqual(a.select_profile(stats,False),"ENGINE")
   self.assertGreater(stats["ENGINE"]["n"],stats["BALANCED"]["n"])
   db.close()
 def test_no_training_on_holdout_failures_or_other_decks(self):
  with tempfile.TemporaryDirectory() as td:
   db=a.connect(Path(td)/"m.sqlite")
   for i,(ctx,mode,status,reward) in enumerate([("other","train","completed",1),("deck","evaluate","completed",None),("deck","train","engine_error",None)]):
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,ctx,mode,i,"ENGINE",status,reward,"{}"))
   self.assertTrue(all(s["n"]==0 for s in a.statistics(db,"deck").values()))
   self.assertEqual(a.select_profile(a.statistics(db,"deck"),False),"BALANCED");db.close()
 def test_metrics_separate_own_turns_opponent_damage_and_life_payment(self):
  own="Ai(1)-GGS_Current"
  metrics=a.effects(["Turn: Turn 1 ("+own+")",
   "Damage: Ninja (1) deals 3 combat damage to Ai(2)-Jaymie_Ezio.",
   "Damage: Ninja (1) deals 10 non-combat damage to Ai(2)-Jaymie_Ezio.",
   "Add To Stack: "+own+" triggered Goro-Goro and Satoru",
   "Life: Life: "+own+" 40 > 38","Life: Life: "+own+" 38 > 41",
   "Turn: Turn 2 (Ai(2)-Jaymie_Ezio)",
   "Damage: Assassin (2) deals 20 combat damage to Ai(3)-Gabe_Food."],own)
  self.assertEqual(metrics,{"own_turns":1,"ggs_triggers":1,"opponent_combat_damage_on_own_turn":3,"life_gained":3})
  self.assertGreater(a.utility(metrics,False),a.utility({**metrics,"ggs_triggers":0},False))
 def test_missing_trace_does_not_create_reward(self):
  with self.assertRaises(ValueError):a.effects([],"Ai(1)-GGS_Current")
 def test_unreviewed_high_reward_cannot_enter_reviewed_policy(self):
  with tempfile.TemporaryDirectory() as td:
   db=a.connect(Path(td)/"m.sqlite")
   for i in range(3):
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,"deck","train",i,"ECONOMY","completed",1,"{}"))
   db.commit()
   self.assertEqual(a.statistics(db,"deck")["ECONOMY"]["n"],3)
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],0)
   record_review(db,"fixture",0,"reject","fixture integrity","Deliberate corrupted-feedback fixture","test")
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],0)
   record_review(db,"fixture",1,"pass","fixture feedback","Known controlled feedback","test")
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],1)
   self.assertEqual(a.select_profile(a.statistics(db,"deck",True),False),"BALANCED")
   db.close()
 def test_failed_or_heldout_episode_cannot_be_approved_for_training(self):
  with tempfile.TemporaryDirectory() as td:
   db=a.connect(Path(td)/"m.sqlite")
   for i,(mode,status) in enumerate([("train","engine_error"),("evaluate","completed")]):
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,"deck",mode,i,"ENGINE",status,None,"{}"))
    with self.assertRaises(ValueError):record_review(db,"fixture",i,"pass","test","test","test")
   db.close()

if __name__=="__main__":unittest.main()
