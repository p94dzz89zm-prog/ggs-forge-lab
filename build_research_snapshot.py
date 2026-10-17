#!/usr/bin/env python3
"""Build a closed, provenance-bound Oracle/rulings research snapshot.

Eligibility is a filter of the supplied snapshot, not a gameplay result or a
claim that release/paper availability fields absent from that source exist.
"""
import argparse
from contextlib import closing
from datetime import datetime,timezone
import hashlib,json,os,sqlite3,tempfile
from pathlib import Path
from research_tools import connection

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def build(oracle_source,rulings_source,output):
 oracle_source,rulings_source,output=map(lambda p:Path(p).resolve(),(oracle_source,rulings_source,output))
 if output.exists():raise FileExistsError('Preserve earlier research snapshots: '+str(output))
 inputs={str(p):sha(p) for p in (oracle_source,rulings_source)}
 with closing(connection(oracle_source)) as oracle,closing(connection(rulings_source)) as rules:
  oracle.row_factory=sqlite3.Row;oracle.execute('BEGIN');rules.execute('BEGIN')
  for db in (oracle,rules):
   if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Input database integrity check failed')
  count=oracle.execute('SELECT COUNT(*) FROM cards').fetchone()[0]
  if count==0:raise ValueError('Oracle source has zero cards; rulings alone are not a card database')
  source_meta=dict(oracle.execute('SELECT key,value FROM metadata'))
  if int(source_meta.get('unique_oracle_cards',count))!=count:raise ValueError('Oracle metadata count mismatch')
  output.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=output.parent) as td:
   staged=Path(td)/'snapshot.sqlite'
   with closing(sqlite3.connect(staged)) as target:
    target.executescript('''CREATE TABLE cards(oracle_id TEXT PRIMARY KEY,name TEXT,mana_cost TEXT,mana_value REAL,type_line TEXT,oracle_text TEXT,color_identity TEXT,keywords TEXT,legal_commander TEXT,power TEXT,toughness TEXT,layout TEXT,representative_id TEXT,card_faces_json TEXT,grixis_eligible INTEGER);
CREATE TABLE rulings(id INTEGER PRIMARY KEY,oracle_id TEXT,source TEXT,published_at TEXT,comment TEXT);
CREATE INDEX rulings_oracle ON rulings(oracle_id);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);''')
    eligible=0
    for r in oracle.execute('SELECT * FROM cards ORDER BY oracle_id'):
     colors=set(filter(None,(r['color_identity'] or '').split(',')))
     ok=r['legal_commander']=='legal' and colors<=set('UBR');eligible+=ok
     target.execute('INSERT INTO cards VALUES('+','.join('?' for _ in range(15))+')',(r['oracle_id'],r['name'],r['mana_cost'],r['cmc'],r['type_line'],r['oracle_text'],r['color_identity'],r['keywords'],r['legal_commander'],r['power'],r['toughness'],r['layout'],r['representative_id'],r['card_faces_json'],int(ok)))
    target.executemany('INSERT INTO rulings(oracle_id,source,published_at,comment) VALUES(?,?,?,?)',rules.execute('SELECT oracle_id,source,published_at,comment FROM rulings ORDER BY oracle_id,published_at,comment'))
    stats={'oracle_cards':count,'grixis_commander_eligible':eligible,'rulings':target.execute('SELECT COUNT(*) FROM rulings').fetchone()[0],'cards_with_rulings':target.execute('SELECT COUNT(DISTINCT c.oracle_id) FROM cards c JOIN rulings r USING(oracle_id)').fetchone()[0]}
    if stats['rulings']==0:raise ValueError('Rulings source is empty')
    meta={'format':1,'source_metadata':source_meta,'input_sha256':inputs,'counts':stats,'eligibility':'legal_commander=legal and color_identity subset UBR, including colorless','availability_limit':'Paper games and release dates are absent from this source; released-paper availability requires separate verification.','performance_limit':'Database filtering and Oracle/rulings lookup establish no gameplay strength.','created_utc':datetime.now(timezone.utc).isoformat()}
    target.executemany('INSERT INTO metadata VALUES(?,?)',[(k,json.dumps(v,sort_keys=True)) for k,v in meta.items()]);target.commit()
    assert target.execute('PRAGMA quick_check').fetchone()[0]=='ok'
   if any(sha(Path(p))!=h for p,h in inputs.items()):raise ValueError('Research input changed during build')
   assert not Path(str(staged)+'-journal').exists()
   with staged.open('rb') as stream:os.fsync(stream.fileno())
   os.replace(staged,output)
 return {**meta,'output_sha256':sha(output),'output':str(output)}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('oracle-source','rulings-source','output'):p.add_argument('--'+key,type=Path,required=True)
 a=p.parse_args();print(json.dumps(build(a.oracle_source,a.rulings_source,a.output),indent=2))
if __name__=='__main__':main()
