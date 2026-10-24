import json
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from research_tools import search,observations,engine_provenance,connection
from policy_search import parent_candidate,sample_vector,BASE,BOUNDS


class ResearchTests(unittest.TestCase):
 def test_read_only_search_refuses_an_interrupted_transaction(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'interrupted.sqlite'
   code='''import os,sqlite3,sys
db=sqlite3.connect(sys.argv[1])
db.execute('PRAGMA journal_mode=DELETE')
db.execute('PRAGMA cache_size=1')
db.execute('CREATE TABLE records(id INTEGER PRIMARY KEY,value TEXT)')
db.executemany('INSERT INTO records VALUES(?,?)',[(i,'committed'*300) for i in range(80)])
db.commit()
db.execute('BEGIN IMMEDIATE')
db.execute("UPDATE records SET value='uncommitted'||value")
os._exit(0)
'''
   subprocess.run([sys.executable,'-c',code,str(path)],check=True)
   journal=Path(str(path)+'-journal');self.assertTrue(journal.exists());self.assertNotEqual(journal.read_bytes()[:8],bytes(8))
   db=connection(path)
   try:
    with self.assertRaises(sqlite3.OperationalError):db.execute('SELECT value FROM records').fetchall()
   finally:db.close()
 def test_search_separates_eligibility_and_engine_evidence(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'index.sqlite';db=sqlite3.connect(path)
   db.executescript('CREATE TABLE cards(oracle_id TEXT,name TEXT,grixis_eligible INTEGER,in_deck INTEGER,mana_value REAL,engine_definition_present INTEGER); CREATE VIRTUAL TABLE search USING fts5(name,rules_text,oracle_id UNINDEXED); CREATE TABLE role_matches(oracle_id TEXT,role TEXT,matched_text TEXT);')
   db.executemany('INSERT INTO cards VALUES(?,?,?,?,?,?)',[('a','Eligible',1,0,2,0),('b','Off color',0,0,1,1)])
   db.executemany('INSERT INTO search VALUES(?,?,?)',[('Eligible','Flying','a'),('Off color','Flying','b')]);db.execute('INSERT INTO role_matches VALUES(?,?,?)',('a','combat_access','Flying'));db.commit();db.close()
   rows=search(path,'Flying',['combat_access']);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['engine_definition_present'],0);self.assertEqual(rows[0]['role_evidence'][0]['matched_text'],'Flying')
 def test_priority_observations_do_not_count_repeated_snapshots_as_turns(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'audit.jsonl';own={'id':0,'life':40,'hand_count':1,'hand':[{'name':'Held protection'}],'battlefield':[]}
   state={'viewer_id':0,'active_player_id':0,'turn':12,'phase':'MAIN1','players':[own]}
   row={'kind':'priority','state':state,'decision':{'action':'pass'}};p.write_text(json.dumps(row)+'\n'+json.dumps(row)+'\n')
   turns,seen,held=observations(p);self.assertEqual(len(turns),1);self.assertEqual(seen,held);self.assertEqual(held,{'Held protection'})
 def test_integrity_withheld_feedback_cannot_select_a_parent(self):
  candidates=[{'games':[{'status':'completed','won':True,'feedback':None}]}]
  self.assertIsNone(parent_candidate(candidates,random.Random(1)))
 def test_parameter_search_is_reproducible_and_bounded(self):
  self.assertEqual(sample_vector(random.Random(9)),sample_vector(random.Random(9)))
  for seed in range(100):
   for parent in [None,BASE]:
    vector=sample_vector(random.Random(seed),parent)
    self.assertTrue(all(lo<=vector[k]<=hi for k,(lo,hi) in BOUNDS.items()))
 def test_engine_versions_remain_explicit(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'manifest.json').write_text(json.dumps({'jar_sha256':'old-build'}))
   record=root/'attempt'/'engine-records'/'label'/'1.json';record.parent.mkdir(parents=True);record.write_text('{}')
   self.assertEqual(engine_provenance(record),'old-build')


if __name__=='__main__':unittest.main()
