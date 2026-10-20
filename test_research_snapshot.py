import json,sqlite3,tempfile,unittest
from pathlib import Path
from build_research_snapshot import build

class SnapshotTests(unittest.TestCase):
 def inputs(self,root,empty=False):
  oracle=root/'oracle.sqlite';rules=root/'rules.sqlite'
  with sqlite3.connect(oracle) as d:
   d.executescript('CREATE TABLE cards(oracle_id TEXT,name TEXT,mana_cost TEXT,cmc REAL,type_line TEXT,oracle_text TEXT,color_identity TEXT,keywords TEXT,legal_commander TEXT,power TEXT,toughness TEXT,layout TEXT,representative_id TEXT,card_faces_json TEXT);CREATE TABLE metadata(key TEXT,value TEXT);')
   if not empty:
    for oid,color,legal in [('blue','U','legal'),('colorless','','legal'),('white','W','legal'),('banned','B','banned')]:d.execute('INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,oid,'{1}',1,'Creature','test',color,'[]',legal,'1','1','normal',oid,'[]'))
  with sqlite3.connect(rules) as d:d.execute('CREATE TABLE rulings(oracle_id TEXT,source TEXT,published_at TEXT,comment TEXT)');d.execute('INSERT INTO rulings VALUES(?,?,?,?)',('blue','wotc','2020-01-01','Test ruling'))
  return oracle,rules
 def test_join_eligibility_provenance_and_closed_output(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);o,r=self.inputs(root);out=root/'snapshot.sqlite';result=build(o,r,out)
   self.assertEqual(result['counts']['oracle_cards'],4);self.assertEqual(result['counts']['grixis_commander_eligible'],2)
   self.assertEqual(result['counts']['cards_with_rulings'],1);self.assertEqual(len(result['output_sha256']),64)
   self.assertFalse(Path(str(out)+'-journal').exists())
   with sqlite3.connect(out) as d:
    self.assertEqual(d.execute('PRAGMA quick_check').fetchone()[0],'ok');self.assertEqual(d.execute('SELECT comment FROM rulings').fetchone()[0],'Test ruling')
    self.assertIn(str(o),json.loads(d.execute("SELECT value FROM metadata WHERE key='input_sha256'").fetchone()[0]))
 def test_empty_card_table_is_not_mistaken_for_full_oracle_data(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);o,r=self.inputs(root,empty=True);out=root/'snapshot.sqlite'
   with self.assertRaisesRegex(ValueError,'zero cards'):build(o,r,out)
   self.assertFalse(out.exists())
 def test_previous_completed_snapshot_cannot_be_overwritten(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);o,r=self.inputs(root);out=root/'snapshot.sqlite';out.write_bytes(b'preserved')
   with self.assertRaises(FileExistsError):build(o,r,out)
   self.assertEqual(out.read_bytes(),b'preserved')
