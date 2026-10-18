#!/usr/bin/env python3
"""Bounded paired evaluation with private records and fail-closed resume.

No model update. Record integrity permits diagnostic comparison, not trusted
learning. An unknown in-flight attempt is never automatically re-executed.
"""
import argparse
import fcntl
import hashlib
import json
import zipfile
from pathlib import Path
import dragonmind
from adaptive_pilot import atomic_json
from population_protocol import specification
from referee_games import inspect
from learning_gate import assess


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_saved(root,entry):
 for relative,expected in entry['evidence_sha256'].items():
  p=(root/relative).resolve()
  if not p.is_relative_to(root.resolve()) or sha(p)!=expected:raise ValueError('Saved evidence changed: '+relative)
def summary(state):
 rows=state['attempts'];complete=[a for a in rows if a.get('complete')]
 return {'attempts':len(rows),'completed':len(complete),'independent_seed_clusters':len({a['game']['seed'] for a in complete}),
  'rules_reviewed_games':sum(a['learning_gate']['status']=='approved_for_learning' for a in complete),
  'trusted_training_updates':0,'strategic_strength_verdict':'Not established; full-game review and sufficient independent paired conditions required',
  'all_completed':len(complete)==2,'outcomes':[{'pilot':a['label'],'status':a.get('game',{}).get('status','running'),'winner':a.get('game',{}).get('winner'),'engine_ms':a.get('game',{}).get('engine_ms'),'review':a.get('learning_gate',{}).get('status','pending')} for a in rows]}
def run(a):
 for jar in (a.baseline,a.candidate):
  with zipfile.ZipFile(jar) as z:
   if z.testzip() is not None:raise ValueError('Corrupt engine input')
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
 pop=specification(a.engine,a.population);names=[a.deck,'Jaymie_Ezio','Gabe_Food','Destyn_Turtles'];builds={'baseline':a.baseline,'candidate':a.candidate}
 protocol={'format':1,'purpose':a.purpose,'seed':a.seed,'rotation':a.rotation,'timeout':a.timeout,'deck':a.deck,'deck_sha256':{n:sha(dragonmind.ROOT/'decks'/(n+'.dck')) for n in names},'engine_sha256':{k:sha(v) for k,v in builds.items()},'population':pop,'logging':'all_seats_private_offline','flags':['-Ddragonmind.boundedCombatForecast=true','-Ddragonmind.linePlanner=false'],'collector_source_sha256':sha(Path(dragonmind.__file__)),'batch_source_sha256':sha(Path(__file__))}
 if a.purpose=='heldout' and a.population!='unseen_evaluation':raise ValueError('Heldout batch requires heldout opponent population')
 with (out/'cycle.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  path=out/'state.json'
  if path.exists():
   state=json.loads(path.read_text())
   if state['protocol']!=protocol:raise ValueError('Input provenance changed; use a separately allocated attempt')
   for entry in state['attempts']:
    if entry['status']=='running':raise RuntimeError('Unknown in-flight outcome; preserve and reconcile before resuming')
    verify_saved(out/entry['label'],entry)
   if any(not e['complete'] for e in state['attempts']):raise RuntimeError('Prior failed attempt retained; no automatic retry')
  else:state={'protocol':protocol,'attempts':[]};atomic_json(path,state)
  for label,jar in builds.items():
   if any(e['label']==label for e in state['attempts']):continue
   root=out/label;root.mkdir(exist_ok=False);entry={'label':label,'status':'running'};state['attempts'].append(entry);atomic_json(path,state)
   row=dragonmind.batch(a.engine.resolve(),jar.resolve(),root,a.deck,a.rotation,[a.seed],a.timeout,True,True,extra_jvm_flags=tuple(protocol['flags']),audit_all_seats=True,ai_profiles=pop['profiles_by_unrotated_deck'])[0]
   atomic_json(root/'attempt.json',row)
   signature={'purpose':a.purpose,'jar_sha256':protocol['engine_sha256'][label],'deck_sha256':protocol['deck_sha256'],'opponent_population':pop}
   try:reports=inspect(root)
   except (ValueError,OSError,KeyError,TypeError):reports=[]
   gate=assess(root,row,reports,signature,{},None)
   hashes={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and (p.suffix in ('.json','.jsonl','.log')) and 'runtime-home' not in p.parts}
   entry.update(status='saved',game=row,learning_gate=gate,integrity_report=reports,evidence_sha256=hashes,complete=row['status'] in ('completed','completed_draw') and len(reports)==1 and reports[0].get('record_integrity_passed',False))
   if sha(jar)!=protocol['engine_sha256'][label] or any(sha(dragonmind.ROOT/'decks'/(n+'.dck'))!=h for n,h in protocol['deck_sha256'].items()):entry['complete']=False;entry['input_error']='Inputs changed during execution'
   atomic_json(path,state);atomic_json(out/'summary.json',summary(state));print(label,row['status'],'complete=',entry['complete'],flush=True)
   if not entry['complete']:return 1
  atomic_json(out/'summary.json',summary(state));return 0

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('engine','baseline','candidate','output'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--seed',type=int,required=True);p.add_argument('--rotation',type=int,choices=range(4),default=0);p.add_argument('--timeout',type=int,default=120);p.add_argument('--deck',default='GGS_Apex_20261017_Whip');p.add_argument('--population',choices=('stock','diverse_training','unseen_evaluation'),default='diverse_training');p.add_argument('--purpose',choices=('development','heldout'),default='development');a=p.parse_args()
 if not 1<=a.timeout<=180:p.error('Budget must be1..180 seconds per game')
 if a.seed<0:p.error('Nonnegative allocated seed required')
 raise SystemExit(run(a))
if __name__=='__main__':main()
