from pathlib import Path
import json,re,collections,hashlib
import argparse
parser=argparse.ArgumentParser(description='Summarize two audited Apex/Layered pod runs without replaying games')
parser.add_argument('run_directory',type=Path)
root=parser.parse_args().run_directory.resolve()
results={}
for variant,directory in [('current-apex','current-apex'),('layered','layered')]:
 run=root/directory;log=next(run.glob('*.log'));lines=log.read_text().splitlines();summary=json.loads((run/'summary.json').read_text())[0];name=summary['seats'][0];player='Ai(1)-'+name
 turn=0;own_turns=[];actions=[];damage=collections.defaultdict(lambda:collections.Counter());triggers=collections.Counter();category=collections.Counter();commander_casts=[];ninjustu_activations=[]
 for l in lines:
  category[l.split(':',1)[0]]+=1
  m=re.match(r'Turn: Turn (\d+) \((.*)\)',l)
  if m:
   turn=int(m[1])
   if m[2]==player:own_turns.append(turn)
  if l.startswith('Add To Stack: '+player):
   actions.append({'turn':turn,'line':l})
   if l=='Add To Stack: '+player+' cast Goro-Goro and Satoru':commander_casts.append({'global_turn':turn,'own_turn_number':own_turns.index(turn)+1})
   if ' triggered ' in l:triggers[l.split(' triggered ',1)[1].split(' targeting ',1)[0]]+=1
  m=re.match(r'Damage: (.+?) \((\d+)\) deals (\d+) (non-combat|combat) damage to (.+)\.',l)
  if m:damage[m[1]][m[5]]+=int(m[3])
 priority={};evaluation={};gstates=[];main_snapshots={};cards_seen=collections.Counter()
 for p in (run/'audit').rglob('seat-*.jsonl'):
  rows=[json.loads(l) for l in p.open()];priority[p.stem]=len(rows)
  if p.name=='seat-0.jsonl':
   gstates=rows
   for r in rows:
    state=r['state'];me=next(q for q in state['players'] if q['id']==0)
    for card in me.get('hand',[]):cards_seen[card['name']]+=1
    if state['active_player_id']==0 and state['phase']=='MAIN1' and state['turn'] not in main_snapshots:
     main_snapshots[state['turn']]={'life':me['life'],'hand':[c['name'] for c in me.get('hand',[])],'battlefield':[{'name':c['name'],'tapped':c['tapped'],'type':c['type']} for c in me['battlefield']]}
 for p in (run/'audit').rglob('evaluation-seat-*.jsonl'):
  rows=[json.loads(l) for l in p.open()];evaluation[p.stem]={'rows':len(rows),'decisions':dict(collections.Counter(r['decision'] for r in rows))}
  if p.name=='evaluation-seat-0.jsonl':commander_evaluations=[r for r in rows if 'Goro-Goro and Satoru - Creature' in r['ability']]
 first=gstates[0]['state'];me=next(p for p in first['players'] if p['id']==0)
 outcome={'summary':summary,'performance':json.loads((run/'performance.json').read_text()),'metadata':json.loads((run/'metadata.json').read_text()),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'own_turns':own_turns,'commander_casts':commander_casts,'opening_hand':[c['name'] for c in me['hand']],'stack_actions':actions,'trigger_counts':dict(triggers),'logged_damage_by_source':{n:dict(v) for n,v in damage.items()},'log_category_counts':dict(category),'priority_counts':priority,'evaluation_counts':evaluation,'audit_bytes':sum(p.stat().st_size for p in (run/'audit').rglob('*.jsonl')),'main1_first_snapshot_per_own_turn':main_snapshots,'commander_evaluations':commander_evaluations,'hand_card_snapshot_occurrences':dict(cards_seen)}
 results[variant]=outcome
 print(variant,'summary',summary['winner'],summary['engine_ms'],summary['last_logged_turn'],'ownTurns',len(own_turns),'commander',commander_casts)
 print('triggers',triggers);print('priority',sum(priority.values()),'eval',sum(r['rows'] for r in evaluation.values()),'auditMB',outcome['audit_bytes']/1e6)
 print('opening',outcome['opening_hand']);print('main snapshots',json.dumps(main_snapshots)[:2200]);print('damage source',json.dumps(outcome['logged_damage_by_source'].get('Purphoros, God of the Forge')))
(root/'analysis.json').write_text(json.dumps(results,indent=2)+'\n')
