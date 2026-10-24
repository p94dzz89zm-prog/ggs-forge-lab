import sqlite3,tempfile,unittest
from pathlib import Path
from apex_static_audit import audit,resolve

class BaselineValidationTests(unittest.TestCase):
 def database(self,path):
  db=sqlite3.connect(path);db.execute('CREATE TABLE cards(name TEXT,legal_commander TEXT,grixis_eligible INTEGER)')
  db.executemany('INSERT INTO cards VALUES(?,?,?)',[('Goro-Goro and Satoru','legal',1),('White Card','legal',0),('Banned Card','banned',1),('Fell the Profane // Fell Mire','legal',1)])
  db.commit();db.close()
 def test_zero_quantity_is_rejected_before_resolution(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);db=root/'db';self.database(db);baseline=root/'deck';baseline.write_text('0 Goro-Goro and Satoru\n')
   with self.assertRaisesRegex(ValueError,'Positive card quantities'):audit(db,baseline,root/'out')
 def test_off_identity_and_banned_cannot_enter_baseline(self):
  for name in ('White Card','Banned Card'):
   with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
    root=Path(td);db=root/'db';self.database(db);baseline=root/'deck';baseline.write_text('1 '+name+'\n')
    with self.assertRaisesRegex(ValueError,'identity/legality'):audit(db,baseline,root/'out')
 def test_mdfc_front_name_resolves_to_full_oracle_identity(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'db';self.database(path);db=sqlite3.connect(path);db.row_factory=sqlite3.Row
   self.assertEqual(resolve(db,'Fell the Profane')['name'],'Fell the Profane // Fell Mire')
   db.close()

if __name__=='__main__':unittest.main()
