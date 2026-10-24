#!/usr/bin/env python3
"""Private persistent evidence registry and dashboard export, no invented scores."""
import argparse,datetime,hashlib,json,sqlite3
from pathlib import Path
from evaluation_batch import verify_saved
from referee_games import inspect
from learning_gate import assess

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def connect(path):
 db=sqlite3.connect(path);db.execute('PRAGMA synchronous=FULL');db.execute('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY,kind TEXT,cycle INTEGER,pilot TEXT,data TEXT,source_sha256 TEXT)');db.commit();return db

def record(db,key,kind,cycle,pilot,data,digest):
 old=db.execute('SELECT source_sha256,data FROM events WHERE id=?',(key,)).fetchone()
 if old and (old[0]!=digest or old[1]!=json.dumps(data,sort_keys=True)):raise ValueError('Evidence ID changed; preserve the old event and allocate a new ID')
 db.execute('INSERT OR IGNORE INTO events VALUES(?,?,?,?,?,?)',(key,kind,cycle,pilot,json.dumps(data,sort_keys=True),digest));db.commit()

def import_technical(db,root,cycle):
 p=Path(root)/'validation.json';d=json.loads(p.read_text())
 for entry in d['suites']:
  log=Path(root)/(entry['suite']+'.log')
  if sha(log)!=entry['log_sha256']:raise ValueError('Technical log changed')
  markers=[l for l in log.read_text(errors='replace').splitlines() if l.startswith('Checks passed:')]
  if entry['passed'] and markers!=[f"Checks passed: {entry['expected']}"]:raise ValueError('Missing exact completion marker')
 record(db,f'technical:{cycle}:{d["jar_sha256"]}:{p.parent.name}','technical',cycle,d['jar_sha256'],{'all_passed':d['all_passed'],**d['completed_evidence']},sha(p))

def import_pair(db,root,cycle):
 root=Path(root);p=root/'state.json';state=json.loads(p.read_text());protocol=state['protocol']
 for e in state['attempts']:
  if e['status']=='running':continue
  attempt=root/e['label'];verify_saved(attempt,e);row=e['game'];signature={'purpose':protocol['purpose'],'jar_sha256':protocol['engine_sha256'][e['label']],'deck_sha256':protocol['deck_sha256'],'opponent_population':protocol['population']}
  review=attempt/'learning-review.json';gate=assess(attempt,row,inspect(attempt),signature,{},json.loads(review.read_text()) if review.exists() else None)
  complete=e['complete'];won=(row.get('winner')==f"Ai({row['seats'].index(row['variant'])+1})-{row['variant']}") if complete else None
  record(db,f'game:{cycle}:{e["label"]}:{row["seed"]}:{row["seat_rotation"]}','game',cycle,signature['jar_sha256'],{'label':e['label'],'status':row['status'],'complete':complete,'seed':row['seed'],'seat':row['seat_rotation'],'deck':row['variant'],'deck_sha256':signature['deck_sha256'][row['variant']],'population':protocol['population']['name'],'profile_sha256':protocol['population']['profile_sha256'],'won':won,'engine_ms':row.get('engine_ms'),'review':gate['status'],'learning_feedback':None},sha(p))

def validated_rates(games):
 groups={}
 for e in games:
  if e.get('complete') and e.get('review')=='approved_for_learning':
   key=(e['pilot'],e['deck_sha256'],e['population']);groups.setdefault(key,[]).append(e)
 return [{'pilot':k[0],'deck_sha256':k[1],'population':k[2],'games':len(v),'wins':sum(e['won'] for e in v),'win_rate':sum(e['won'] for e in v)/len(v),'independent_seed_clusters':len({e['seed'] for e in v})} for k,v in groups.items()]


def export(db,ledger,output,python_tests=None,decision=None):
 ledger=Path(ledger);d=json.loads(ledger.read_text());events=[{'id':r[0],'kind':r[1],'cycle':r[2],'pilot':r[3],**json.loads(r[4]),'source_sha256':r[5]} for r in db.execute('SELECT * FROM events ORDER BY cycle,id')]
 games=[e for e in events if e['kind']=='game'];history=[]
 for c in d['cycles']:
  if c['cycle']<15:continue
  technical=c.get('technical',c.get('engine',{}));history.append({'cycle':c['cycle'],'source_commit':c.get('source_commit'),'engine_groups':None if c.get('technical_evidence_integrity',{}).get('status')=='quarantined_partial' else technical.get('summed_engine_checks',technical.get('check_groups_passed')),'python_tests':technical.get('python_tests',c.get('python_tests')),'random_positions':technical.get('fresh_randomized_positions',technical.get('randomized_positions_passed')),'evidence_type':c.get('technical_evidence_integrity',{}).get('status','Saved ledger report; not newly replayed')})
 data={'schema_version':1,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ledger_sha256':sha(ledger),'source_commit':d['source_commit'],'last_saved_cycle':d['last_completed_cycle'],'active_cycle':d.get('active_cycle',{}),'background_training':'Inactive; no scheduled private training runner is configured','trusted_training_updates':sum(e.get('learning_feedback') is not None for e in games),'validated_win_rates':validated_rates(games),'events':events,'games':games,'history':history,'python_tests':python_tests,'decision_comparison':decision,'known_errors':d['known_reproducible_pilot_errors'][-3:],'limitations':['Cycle17 historical engine log gap: MarchDefense log hash mismatch/missing marker; quarantined. Cycle18 independently passes with matching logs.','Tactical bug fixes are separate from measured general strategic improvement.','Archived pod deck proxies and native pilots are not verified current human lists or expert pilots.','No verified combo/control/tempo specialist or learned opponent population yet.','Full-game review is pending; raw outcomes do not train or justify card swaps.','Physical Mistblade displacement and physical land inventory remain unresolved.'],'training':{'method':'Persistent reviewed contextual bandit over three bounded GGS profiles; Java policy guards and optional bounded search','checkpoint_sha256':d.get('cycles',[])[-1].get('model_sha256',d.get('cycles',[])[-1].get('model_sha256_unchanged')),'status':'No new trusted outcome updates; this is not a broad neural Commander learner'},'deck_finding':{'out':'Breath of Fury','in':'Whip of Erebos','verdict':'Experimental','gain':'Repeatable lifelink and paid graveyard recovery without GGS','loss':'Extra-combat chain potential','evidence':'Actual paid constructed recovery; no causal whole-deck strength evidence'}}
 Path(output).write_text(json.dumps(data,indent=2)+'\n');return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--technical',action='append',default=[],help='CYCLE:directory');p.add_argument('--pair',action='append',default=[],help='CYCLE:directory');a=p.parse_args();db=connect(a.db)
 for x in a.technical:n,path=x.split(':',1);import_technical(db,path,int(n))
 for x in a.pair:n,path=x.split(':',1);import_pair(db,path,int(n))
 export(db,a.ledger,a.output);db.close()
if __name__=='__main__':main()
