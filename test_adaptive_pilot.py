import tempfile
import unittest
import hashlib
import json
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
 def test_collector_distinguishes_engine_error_from_normal_control_change(self):
  self.assertEqual(a.eligible_reward("Correcting zone for Hithlain Rope (227)",1.0),1.0)
  self.assertIsNone(a.eligible_reward("java.lang.IllegalStateException: injected",1.0))
  self.assertEqual(a.eligible_reward("ordinary completed game",.3),.3)
 def test_unreviewed_high_reward_cannot_enter_reviewed_policy(self):
  with tempfile.TemporaryDirectory() as td:
   db=a.connect(Path(td)/"m.sqlite")
   for i in range(3):
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,"deck","train",i,"ECONOMY","completed",1,"{}"))
   db.commit()
   self.assertEqual(a.statistics(db,"deck")["ECONOMY"]["n"],3)
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],0)
   record_review(db,"fixture",0,"reject","fixture integrity","Deliberate corrupted-feedback fixture","test")
   self.assertEqual(a.statistics(db,"deck")["ECONOMY"]["n"],2)
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],0)
   with self.assertRaises(ValueError):record_review(db,"fixture",1,"pass","fixture feedback","Missing canonical evidence","test")
   self.assertEqual(a.statistics(db,"deck",True)["ECONOMY"]["n"],0)
   self.assertEqual(a.select_profile(a.statistics(db,"deck",True),False),"BALANCED")
   db.close()
 def test_failed_or_heldout_episode_cannot_be_approved_for_training(self):
  with tempfile.TemporaryDirectory() as td:
   db=a.connect(Path(td)/"m.sqlite")
   for i,(mode,status) in enumerate([("train","engine_error"),("evaluate","completed")]):
    db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",("fixture",i,"deck",mode,i,"ENGINE",status,None,"{}"))
    with self.assertRaises(ValueError):record_review(db,"fixture",i,"pass","test","test","test")
   db.close()

class EvidenceFaultTests(unittest.TestCase):
 def fixture(self,td):
  root=Path(td)/"run";attempt=root/"attempt-000000";attempt.mkdir(parents=True)
  db=a.connect(Path(td)/"model.sqlite")
  record={"seed":77,"status":"completed","winner":"Ai(2)-Jaymie_Ezio","engine_ms":12}
  lines=["Turn: Turn 1 (Ai(1)-GGS_Current)","Damage: Ninja (1) deals 3 combat damage to Ai(2)-Jaymie_Ezio.","Add To Stack: Ai(1)-GGS_Current triggered Goro-Goro and Satoru"]
  transcript=attempt/"game.log";transcript.write_text("\n".join(lines)+"\nDragonMind Result: "+json.dumps(record)+"\n")
  result=attempt/"game.json";result.write_text(json.dumps(record))
  (attempt/"console.log").write_text(transcript.read_text())
  metrics=a.effects(lines,"Ai(1)-GGS_Current")
  evidence={"game":{**record,"variant":"GGS_Current","seats":["GGS_Current","Jaymie_Ezio","Gabe_Food","Destyn_Turtles"],"engine_record":"game.json","engine_transcript":"game.log","log":"console.log"},"metrics":metrics,"record_sha256":a.sha(result),"transcript_sha256":a.sha(transcript),"console_sha256":a.sha(attempt/"console.log")}
  db.execute("INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?)",(str(root),0,"fixture","train",77,"BALANCED","completed",a.utility(metrics,False),json.dumps(evidence)));db.commit()
  return db,root,attempt,evidence
 def test_complete_consistent_fixture_can_receive_scoped_review(self):
  with tempfile.TemporaryDirectory()as td:
   db,root,_,_=self.fixture(td);record_review(db,str(root),0,"pass","synthetic fixture","Integrity fixture, not empirical game evidence","test")
   self.assertEqual(a.statistics(db,"fixture",True)["BALANCED"]["n"],1);db.close()
 def rejection(self,mutation):
  with tempfile.TemporaryDirectory()as td:
   db,root,attempt,evidence=self.fixture(td);mutation(db,attempt,evidence)
   db.execute("UPDATE episodes SET evidence=?",(json.dumps(evidence),));db.commit()
   with self.assertRaises(ValueError):record_review(db,str(root),0,"pass","fault fixture","Deliberately corrupted fixture","test")
   self.assertEqual(a.statistics(db,"fixture",True)["BALANCED"]["n"],0);db.close()
 def test_changed_transcript_rejected(self):
  self.rejection(lambda db,p,e:(p/"game.log").write_text("tampered"))
 def test_changed_record_rejected(self):
  self.rejection(lambda db,p,e:(p/"game.json").write_text("{}"))
 def test_forged_metrics_rejected(self):
  self.rejection(lambda db,p,e:e["metrics"].update(ggs_triggers=100))
 def test_forged_reward_rejected(self):
  self.rejection(lambda db,p,e:db.execute("UPDATE episodes SET reward=1"))
 def test_path_escape_rejected(self):
  self.rejection(lambda db,p,e:e["game"].update(engine_record="../outside.json"))
 def test_duplicate_completion_marker_rejected(self):
  def change(db,p,e):
   path=p/"game.log";last=path.read_text().splitlines()[-1];path.write_text(path.read_text()+last+"\n");e["transcript_sha256"]=a.sha(path)
  self.rejection(change)
 def test_engine_error_after_completion_rejected(self):
  def change(db,p,e):
   path=p/"game.log";path.write_text(path.read_text()+"java.lang.IllegalStateException: injected\n");e["transcript_sha256"]=a.sha(path)
  self.rejection(change)
 def test_changed_console_rejected(self):
  self.rejection(lambda db,p,e:(p/"console.log").write_text("tampered"))
 def test_normal_control_change_diagnostic_does_not_poison_integrity(self):
  with tempfile.TemporaryDirectory()as td:
   db,root,p,e=self.fixture(td);path=p/"console.log";path.write_text(path.read_text()+"Correcting zone for Hithlain Rope (227)\n");e["console_sha256"]=a.sha(path)
   db.execute("UPDATE episodes SET evidence=?",(json.dumps(e),));db.commit()
   record_review(db,str(root),0,"pass","synthetic fixture","Ordinary controller-change diagnostic; not empirical game evidence","test")
   self.assertEqual(a.statistics(db,"fixture",True)["BALANCED"]["n"],1);db.close()
 def test_reported_winner_disagreement_rejected(self):
  self.rejection(lambda db,p,e:e["game"].update(winner="Ai(1)-GGS_Current"))

if __name__=="__main__":unittest.main()
