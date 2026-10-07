"""Extract observed progression from Forge priority snapshots and canonical transcripts."""
import json,re,hashlib,statistics,collections,sys,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AMPS={'Purphoros, God of the Forge','Dragon Tempest','Roaming Throne','Karlach, Fury of Avernus','Port Razer','Aggravated Assault','Annie Joins Up'}
FACTORIES={'Kari Zev, Skyship Raider','Loyal Apprentice','Lagomos, Hand of Hatred','Urabrask\'s Forge','Fire Navy Trebuchet','Krenko, Tin Street Kingpin','Reinforced Ronin','Nether Traitor','Alora, Merry Thief'}
ACCESS={'Tetsuko Umezawa, Fugitive','Higure, the Still Wind','Dauthi Trapper','Dauthi Embrace','Break Through the Line','War Cadence'}
ROCKS={'Sol Ring','Arcane Signet','Fellwar Stone','Talisman of Creativity','Talisman of Dominance','Talisman of Indulgence','Goldspan Dragon'}
CREATION='Whenever one or more creatures you control that entered this turn deal combat damage to a player, create a 5/5 red Dragon Spirit'

def extract(directory,row):
 variant=row.get('variant','Pure_GGS');pureidx=row['seats'].index(variant);name=f'Ai({pureidx+1})-{variant}'
 log=(directory/row.get('engine_transcript',row['log'])).read_text(errors='replace')
 audit=directory/'audit'/Path(row['log']).stem/f'seat-{pureidx}.jsonl'
 if not audit.exists():audit=audit.with_suffix('.jsonl.gz')
 metrics={'seed':row['seed'],'rotation':row['seat_rotation'],'status':row['status'],'winner':row.get('winner'),'win':row.get('winner')==name,'final_global_turn':row.get('last_logged_turn'),'engine_seconds':row.get('engine_ms',0)/1000,'log':str(directory/row['log']),'audit':str(audit),'ggs_cast_turn':None,'first_fresh_connection':None,'first_dragon_turn':None,'second_dragon_turn':None,'peak_simultaneous_ggs_dragons':0,'peak_offensive_power':0,'peak_evasive_power':0,'renewable_ammunition_turn':None,'access_turn':None,'card_acceleration_turn':None,'mana_acceleration_turn':None,'basic_turn':None,'strong_turn':None,'threat_turn':None,'amplifiers_seen':[],'artifact_reasons':[]}
 states=[];pureturns={};turncount=0;owner_ids={};all_own_ids=set();seen=set();ggsids=set();copyids=set();prev=None;prevbf={};lasttop={};events=[];draws=0;treasures=0;wipe_events=[];lastcast=None;removed_ggs=[];audit_amp_events=[];combat_counts=collections.Counter();combat_start={};prev_phase=None;chosen_throne=None;ggs_birth_seq={};audit_haste_events=[]
 with (gzip.open(audit,'rt') if audit.suffix=='.gz' else audit.open()) as stream:
  for line in stream:
   x=json.loads(line);s=x.get('state');
   if x.get('kind')=='type' and x.get('decision',{}).get('card')=='Roaming Throne':chosen_throne=x['decision'].get('chosen_type')
   if not s:continue
   turn=s['turn'];phase=s['phase'];
   pure=next((p for p in s['players'] if p['id']==pureidx),None)
   if pure is None:continue
   if s['active_player_id']==pureidx and turn not in pureturns:
    turncount+=1;pureturns[turn]=turncount
   personal=pureturns.get(turn,turncount)
   bf={c['id']:c for c in pure['battlefield']};names={c['name'] for c in bf.values()};all_own_ids.update(bf)
   for p in s['players']:
    for c in p['battlefield']:owner_ids[(turn,c['id'])]=p['id']
   born={i:c for i,c in bf.items() if i not in seen};seen.update(bf)
   top=s.get('stack',[{}])[0] if s.get('stack') else {}
   if phase=='COMBAT_BEGIN' and prev_phase!=(turn,phase):combat_counts[turn]+=1
   if top.get('name') in AMPS and top.get('controller_id')==pureidx and any(w in top.get('description','') for w in ('Whenever','Untap all','additional combat')):audit_amp_events.append({'name':top['name'],'seq':len(states),'global_turn':turn})
   if top.get('name')=='Goro-Goro and Satoru' and 'gain haste' in top.get('description',''):audit_haste_events.append({'seq':len(states),'global_turn':turn})
   prev_phase=(turn,phase)
   for i in set(bf)-set(prevbf):
    if lasttop.get('name') in FACTORIES and lasttop.get('controller_id')==pureidx and 'Creature' in bf[i]['type'] and (bf[i]['name']!=lasttop['name'] or lasttop['name'] in {'Reinforced Ronin','Nether Traitor'}):events.append({'kind':'factory_ammunition','source':lasttop['name'],'id':i,'turn':personal,'global_turn':turn,'seq':len(states)})
   for i,c in born.items():
    if c['name']=='Dragon Spirit Token':
     if lasttop.get('name')=='Goro-Goro and Satoru' and CREATION in lasttop.get('description',''):
      ggsids.add(i);ggs_birth_seq[i]=len(states);events.append({'kind':'ggs_dragon','id':i,'global_turn':turn,'turn':personal,'seq':len(states),'amp_present':sorted(names&AMPS),'source':lasttop.get('description')})
     else:copyids.add(i);events.append({'kind':'other_dragon','id':i,'global_turn':turn,'turn':personal,'seq':len(states),'source':lasttop.get('name'),'source_player_id':lasttop.get('controller_id')})
    if c['name']=='Treasure Token':treasures+=1
   if prev and pure['hand_count']>prev['hand_count'] and phase!='DRAW' and 'draw' in lasttop.get('description','').lower():
    gain=pure['hand_count']-prev['hand_count'];draws+=gain
    if metrics['card_acceleration_turn'] is None:metrics['card_acceleration_turn']=personal
   creatures=[c for c in bf.values() if 'Creature' in c['type'] and not c.get('phased_out')]
   attackids={a['attacker_id'] for a in s.get('combat',{}).get('attackers',[])}
   ready=[c for c in creatures if not c['summoning_sick'] or 'Haste' in c['keywords'] or c['id'] in attackids]
   def evasion(c):return any(k in c['keywords'] for k in ['Flying','Shadow','Fear','Horsemanship']) or 'can\'t be blocked' in c['rules_text'].lower() or any('can\'t be blocked' in k.lower() for k in c['keywords'])
   power=sum(max(0,c['power']) for c in creatures);epower=sum(max(0,c['power']) for c in ready if evasion(c))
   simultaneous=len(ggsids & set(bf))
   snap={'seq':len(states),'global_turn':turn,'turn':personal,'active':s['active_player_id']==pureidx,'phase':phase,'combat_ordinal':combat_counts[turn],'chosen_throne':chosen_throne,'ggs_dragons':simultaneous,'ggs_total':len(ggsids),'offensive_power':power,'evasive_power':epower,'unblocked_power':sum(max(0,bf[a['attacker_id']]['power']) for a in s.get('combat',{}).get('attackers',[]) if a.get('unblocked') and a['attacker_id'] in bf and a.get('defender_kind')=='player'),'tempest_haste_power':sum(max(0,c['power']) for c in ready if c['id'] in ggsids and c['entered_this_turn'] and 'Haste' in c['keywords'] and c['id'] not in attackids and 'Dragon Tempest' in names and not any(bf.get(i,{}).get('name')=='Lightning Greaves' for i in c['attachments']) and not any(a['global_turn']==turn and a['seq']>ggs_birth_seq[c['id']] for a in audit_haste_events)),'hand':pure['hand_count'],'treasures':sum(c['name']=='Treasure Token' for c in bf.values()),'treasures_created':treasures,'combat_draws':draws,'ggs_present':'Goro-Goro and Satoru' in names,'factories':sorted(names&FACTORIES),'access':sorted(names&ACCESS),'amp_present':sorted(names&AMPS),'creature_count':len(creatures),'mana_sources':sum('Land' in c['type'] for c in bf.values())+sum(c['name'] in ROCKS for c in bf.values()),'fresh_creatures':sum(c['entered_this_turn'] and c['power']>0 for c in creatures),'attacker_count':len(attackids),'fresh_attacking_count':sum(c['entered_this_turn'] and c['power']>0 and c['id'] in attackids for c in creatures),'fresh_ready':sum(c['entered_this_turn'] and c['power']>0 for c in ready),'fresh_unblocked_power':sum(max(0,bf[a['attacker_id']]['power']) for a in s.get('combat',{}).get('attackers',[]) if a.get('unblocked') and a['attacker_id'] in bf and bf[a['attacker_id']]['entered_this_turn'] and a.get('defender_kind')=='player'),'fresh_evasive':sum(c['entered_this_turn'] and c['power']>0 and evasion(c) for c in ready),'life_vector':{p['name']:p['life'] for p in s['players']},'life':pure['life'],'opponent_life':{p['name']:p['life'] for p in s['players'] if p['id']!=pureidx},'top':top.get('name')}
   states.append(snap)
   if snap['active'] and snap['combat_ordinal']>=1 and turn not in combat_start:combat_start[turn]=snap
   if snap['factories'] and metrics['renewable_ammunition_turn'] is None:metrics['renewable_ammunition_turn']=personal
   if (snap['access'] or any(evasion(c) and c['entered_this_turn'] for c in ready)) and metrics['access_turn'] is None:metrics['access_turn']=personal
   if names&ROCKS or treasures:
    if metrics['mana_acceleration_turn'] is None:metrics['mana_acceleration_turn']=personal
   for amp in names&AMPS:
    if amp not in metrics['amplifiers_seen']:metrics['amplifiers_seen'].append(amp)
   if prev:
    prev_creatures={i:c for i,c in prevbf.items() if 'Creature' in c['type'] and not c.get('phased_out')}
    lost=set(prev_creatures)-set(bf)
    if len(lost)>=3 and lasttop.get('name') not in {None,'March of Swirling Mist','Alora, Merry Thief'}:
     wipe_events.append({'turn':personal,'global_turn':turn,'seq':len(states)-1,'lost':len(lost),'power_before':states[-2]['offensive_power'],'ggs_total':len(ggsids),'source':lasttop.get('name'),'source_player_id':lasttop.get('controller_id')})
    if 'Goro-Goro and Satoru' in {c['name'] for c in prevbf.values()} and 'Goro-Goro and Satoru' not in names:
     removed_ggs.append({'turn':personal,'global_turn':turn,'source':lasttop.get('name'),'source_player_id':lasttop.get('controller_id'),'voluntary_reload':lasttop.get('name') in {'Alora, Merry Thief','Grazilaxx, Illithid Scholar'} and lasttop.get('controller_id')==pureidx,'seq':len(states)-1})
   prev={'hand_count':pure['hand_count']};prevbf=bf;lasttop=top
 # Canonical event log and personal turn mapping.
 curglobal=0;curpersonal=0;curphase=None;raw_combat=0;raw_life={f'Ai({i+1})-{d}':40 for i,d in enumerate(row['seats'])};raw_points=[];dragon_hits=[];haste_activations=[];casts=[];damage=collections.Counter();all_damage=collections.Counter();dragon_damage=0;incoming=[];interaction=[];amp_events=[];ggs_resolutions=[];fresh_connections=[];last_add=None
 for lineno,line in enumerate(log.splitlines(),1):
  m=re.match(r'Turn: Turn (\d+) \((.+)\)',line)
  if m:curglobal=int(m[1]);curpersonal=pureturns.get(curglobal,curpersonal);raw_combat=0
  if line.startswith('Phase: '):
   phase_names={'Untap step':'UNTAP','Upkeep step':'UPKEEP','Draw step':'DRAW','Main phase, precombat':'MAIN1','Beginning of Combat Step':'COMBAT_BEGIN','Declare Attackers Step':'COMBAT_DECLARE_ATTACKERS','Declare Blockers Step':'COMBAT_DECLARE_BLOCKERS','First Strike Damage Step':'COMBAT_FIRST_STRIKE_DAMAGE','Combat Damage Step':'COMBAT_DAMAGE','End of Combat Step':'COMBAT_END','Main phase, postcombat':'MAIN2','End step':'END_OF_TURN','Cleanup step':'CLEANUP'}
   curphase=next((v for k,v in phase_names.items() if line.endswith(k)),None)
   if curphase=='COMBAT_BEGIN':raw_combat+=1
   raw_points.append({'global_turn':curglobal,'phase':curphase,'combat_ordinal':raw_combat,'line':lineno,'life':dict(raw_life),'combat_damage':damage[curpersonal],'all_damage':all_damage[curpersonal]})
  life_match=re.match(r'Life: Life: (Ai\(\d+\)-.+?) (-?\d+) >\s*(-?\d+)',line)
  if life_match:
   raw_life[life_match[1]]=int(life_match[3]);raw_points.append({'global_turn':curglobal,'phase':curphase,'combat_ordinal':raw_combat,'line':lineno,'life':dict(raw_life),'combat_damage':damage[curpersonal],'all_damage':all_damage[curpersonal]})
  m=re.match(r'Add To Stack: (Ai\(\d+\)-.+?) (cast|activated|triggered) (.+)',line)
  if m:
   who,kind,desc=m.groups();last_add={'who':who,'kind':kind,'desc':desc,'turn':curpersonal,'global_turn':curglobal,'line':lineno}
   if who==name and kind=='cast' and desc=='Goro-Goro and Satoru':casts.append(curpersonal)
   if who==name and kind=='triggered' and desc.startswith('Goro-Goro and Satoru'):fresh_connections.append(last_add)
   if who==name and kind=='activated' and desc.startswith('Goro-Goro and Satoru'):haste_activations.append({'global_turn':curglobal,'line':lineno})
   if who!=name and 'targeting' in desc and (name in desc or any(owner_ids.get((curglobal,int(i)),pureidx if int(i) in all_own_ids else None)==pureidx for i in re.findall(r'\((\d+)\)',desc))):
    interaction.append({**last_add,'kind':'targeted_interaction'})
   if who==name and any(desc.startswith(a) for a in AMPS) and kind in ('triggered','activated'):
    amp_events.append(last_add)
  if line.startswith('Resolve Stack: '+CREATION):ggs_resolutions.append({'turn':curpersonal,'global_turn':curglobal,'line':lineno})
  m=re.match(r'Damage: (.+) \((\d+)\) deals (\d+) (combat |non-combat )?damage to (Ai\(\d+\)-.+?)\.',line)
  if m:
   card,id_,n,damage_kind,target=m.groups();combat=damage_kind=='combat ';n=int(n);id_=int(id_);sourceowner=owner_ids.get((curglobal,id_))
   if target==name and combat:incoming.append({'turn':curpersonal,'global_turn':curglobal,'amount':n,'source':card,'source_id':sourceowner,'line':lineno})
   if target!=name and sourceowner==pureidx:all_damage[curpersonal]+=n
   if target!=name and sourceowner==pureidx and combat:
    damage[curpersonal]+=n
    if id_ in ggsids:dragon_damage+=n;dragon_hits.append({'id':id_,'global_turn':curglobal,'line':lineno,'amount':n})
   if target!=name and card in AMPS and sourceowner==pureidx and not combat:amp_events.append({'desc':card,'kind':'damage','amount':n,'turn':curpersonal,'global_turn':curglobal,'line':lineno,'who':name})
 # Match priority snapshots to the earliest compatible canonical life state in their exact phase/combat.
 # This prevents later extra-combat damage or activations from leaking into earlier thresholds.
 points_by_phase=collections.defaultdict(list)
 for point in raw_points:points_by_phase[(point['global_turn'],point['phase'],point['combat_ordinal'])].append(point)
 last_line=0
 for snap in states:
  points=points_by_phase.get((snap['global_turn'],snap['phase'],snap['combat_ordinal']),[])
  matches=[q for q in points if q['line']>=last_line and all(q['life'].get(n)==hp for n,hp in snap['life_vector'].items())]
  q=matches[0] if matches else next((q for q in points if q['line']>=last_line),None)
  if q:
   last_line=q['line'];snap['raw_line']=q['line'];snap['observed_combat_damage']=q['combat_damage'];snap['observed_total_damage']=q['all_damage'];snap['life_match']=bool(matches)
  else:snap['raw_line']=last_line;snap['observed_combat_damage']=0;snap['observed_total_damage']=0;snap['life_match']=False
 births=[e for e in events if e['kind']=='ggs_dragon']
 if len(births)==len(ggs_resolutions):
  for e,r in zip(births,ggs_resolutions):e['raw_line']=r['line']
 metrics['ggs_cast_turn']=casts[0] if casts else None
 metrics['first_fresh_connection']=fresh_connections[0]['turn'] if fresh_connections else None
 metrics['fresh_connection_trigger_events']=fresh_connections
 metrics['ggs_cast_turns']=casts;metrics['cumulative_dragons']=len(births);metrics['dragon_damage']=dragon_damage
 metrics['combat_damage_each_turn']=dict(damage);metrics['all_damage_each_turn']=dict(all_damage);metrics['extra_combats_each_turn']={pureturns.get(g):max(0,n-1) for g,n in combat_counts.items() if n>1}
 metrics['resolved_creation_count']=len(ggs_resolutions);metrics['measurement_gaps']=[]
 if len(births)!=len(ggs_resolutions):metrics['measurement_gaps'].append(f'Observed GGS token births {len(births)} vs canonical resolved creations {len(ggs_resolutions)}')
 metrics['reliable_access_confirmed_turn']=next((e['turn'] for e in births if any(b['turn']<e['turn'] for b in births)),None)
 metrics['dragons_each_turn']=dict(collections.Counter(e['turn'] for e in births));metrics['multi_dragon_turn']=next((t for t,n in sorted(metrics['dragons_each_turn'].items()) if n>=2),None)
 for s in states:
  metrics['peak_simultaneous_ggs_dragons']=max(metrics['peak_simultaneous_ggs_dragons'],s['ggs_dragons']);metrics['peak_offensive_power']=max(metrics['peak_offensive_power'],s['offensive_power']);metrics['peak_evasive_power']=max(metrics['peak_evasive_power'],s['evasive_power'])
 if births:
  first=births[0];baseline=states[first['seq']];d1=first['turn'];metrics['first_dragon_turn']=d1
  if len(births)>1:metrics['second_dragon_turn']=births[1]['turn'];metrics['dragon_1_to_2_turns']=births[1]['turn']-d1
  else:metrics['dragon_1_to_2_turns']=None
  for s in states[first['seq']:]:
   growth=s['ggs_dragons']>baseline['ggs_dragons'] or s['offensive_power']>=baseline['offensive_power']+5 or (s['hand']+s['treasures']>=baseline['hand']+baseline['treasures']+2 and s['offensive_power']>=baseline['offensive_power'] and s['combat_draws']+s['treasures_created']>=baseline['combat_draws']+baseline['treasures_created']+2)
   if metrics['basic_turn'] is None and s['ggs_total']>=2 and s['turn']<=d1+2 and growth:metrics['basic_turn']=s['turn'];metrics['basic_seq']=s['seq']
   prior_end=[q for q in states[first['seq']:s['seq']] if q['global_turn']==s['global_turn'] and q['phase']=='COMBAT_END' and q['combat_ordinal']==1]
   extra=bool(s['combat_ordinal']>=2 and prior_end and s['offensive_power']>=prior_end[-1]['offensive_power']+5 and s['ggs_total']>prior_end[-1]['ggs_total'])
   strong=extra or s['ggs_dragons']>=3 or s['evasive_power']>=15 or sum(e['turn']==s['turn'] and e['seq']<=s['seq'] for e in births)>=2 or (s['combat_draws']>=2 and s['treasures_created']>=2 and s['ggs_total']>=2 and s['hand']>=2)
   if metrics['strong_turn'] is None and strong:metrics['strong_turn']=s['turn'];metrics['strong_seq']=s['seq']
   if metrics['threat_turn'] is None and (s['unblocked_power']>=20 or ((s['observed_combat_damage']>=15 or s['observed_total_damage']>=20) and s['phase'] in ('COMBAT_END','MAIN2','END_OF_TURN','CLEANUP'))):metrics['threat_turn']=s['turn'];metrics['threat_seq']=s['seq']
 if births:
  for q in raw_points:
   turn=pureturns.get(q['global_turn'])
   if turn is None or turn<metrics['first_dragon_turn'] or not (q['combat_damage']>=15 or q['all_damage']>=20):continue
   if metrics['threat_turn'] is not None and turn>=metrics['threat_turn']:continue
   candidates=[s for s in states if s['global_turn']==q['global_turn'] and s['active'] and s['combat_ordinal']==q['combat_ordinal']]
   if candidates:
    snap=next((s for s in candidates if s['raw_line']>=q['line']),candidates[-1]);metrics['threat_turn']=turn;metrics['threat_seq']=snap['seq'];metrics['threat_raw_line']=q['line']
 def dependency(label):
  seq=metrics.get(label+'_seq');turn=metrics.get(label+'_turn')
  if seq is None:return None
  snap=states[seq];metrics[label+'_amplifier_present_before']=sorted({a for s in states[:seq+1] for a in s['amp_present']});prior_present={a for s in states[:seq+1] for a in s['amp_present']};contributions=[a for a in amp_events if a['line']<=metrics.get(label+'_raw_line',snap['raw_line']) and a['global_turn']<=snap['global_turn'] and any(a['desc'].startswith(n) for n in prior_present) and any(e['seq']<=seq and e['global_turn']==a['global_turn'] and a['desc'].startswith(e['name']) for e in audit_amp_events)]
  # Throne is independently tested: Human/Goblin selection doubles GGS.
  throne_material=any('Roaming Throne' in e['amp_present'] and (states[e['seq']].get('chosen_throne') in ('Human','Goblin')) and e['seq']<=seq for e in births)
  material=sorted({a['desc'].split(' targeting')[0] for a in contributions if a['kind']=='damage' or a['kind']=='activated' or a['desc'].startswith(('Karlach,','Port Razer'))} | ({'Roaming Throne'} if throne_material else set()))
  # Tempest haste contribution requires same-turn newly created Dragon damage; inspect combat readiness.
  tempest=any('Dragon Tempest' in e['amp_present'] and e['seq']<=seq for e in births)
  if tempest and any(a['desc'].startswith('Dragon Tempest') for a in contributions):material=sorted(set(material)|{'Dragon Tempest'})
  if label in ('basic','strong'):
   material=[a for a in material if a not in ('Purphoros, God of the Forge','Dragon Tempest')]
   if label=='strong' and snap['evasive_power']>=15 and snap['evasive_power']-snap['tempest_haste_power']<15 and snap['ggs_dragons']<3 and sum(e['turn']==snap['turn'] and e['seq']<=seq for e in births)<2 and not (snap['combat_draws']>=2 and snap['treasures_created']>=2 and snap['ggs_total']>=2 and snap['hand']>=2):material=sorted(set(material)|{'Dragon Tempest'})
   # Tempest contributes to Dragon growth only when same-turn fresh Dragons actually connect without another haste source.
   for e in births:
    if e['seq']>seq or 'Dragon Tempest' not in e['amp_present']:continue
    hits=[h for h in dragon_hits if h['id']==e['id'] and h['global_turn']==e['global_turn'] and h['line']<=snap['raw_line']]
    if any(any(b.get('raw_line',0)>h['line'] and b['seq']<=seq and b['global_turn']==e['global_turn'] for b in births) and not any(a['global_turn']==e['global_turn'] and e.get('raw_line',0)<a['line']<h['line'] for a in haste_activations) for h in hits):
     # Greaves may supply redundant haste: leave the cause uncertain rather than asserting necessity.
     material=sorted(set(material)|{'Dragon Tempest'});break
  # Scheduling an extra combat is not yet a contribution to a state reached in the first combat.
  # Require observed additional-combat production, resources, or damage before the threshold.
  extra_names={'Karlach, Fury of Avernus','Port Razer','Aggravated Assault'}
  filtered=[]
  for amp in material:
   if amp not in extra_names:filtered.append(amp);continue
   contributed=False
   for ev in contributions:
    if not ev['desc'].startswith(amp):continue
    extra_states=[q for q in states[:seq+1] if q['global_turn']==ev['global_turn'] and q['active'] and q['combat_ordinal']>=2]
    if not extra_states:continue
    first_extra=extra_states[0];before=[q for q in states[:first_extra['seq']] if q['global_turn']==ev['global_turn'] and q['active'] and q['phase']=='COMBAT_END' and q['combat_ordinal']==1]
    if not before:continue
    base=before[-1]
    if any(q['ggs_total']>base['ggs_total'] or q['combat_draws']>base['combat_draws'] or q['treasures_created']>base['treasures_created'] or (label=='threat' and q['observed_combat_damage']>base['observed_combat_damage']) for q in extra_states):contributed=True
   if contributed:filtered.append(amp)
  material=filtered
  if not material:return {'class':'NATURAL GGS','material_amplifiers':[],'confidence':'observed path, no contributing major amplifier found'}
  # Direct trigger doubling can be subtracted for threshold attribution. Other temporal counterfactuals stay uncertain.
  if material==['Roaming Throne']:
   doubled=collections.Counter((e['global_turn'],states[e['seq']]['combat_ordinal']) for e in births if e['seq']<=seq and 'Roaming Throne' in e['amp_present'] and states[e['seq']].get('chosen_throne') in ('Human','Goblin'))
   ordinary=sum(1 for e in births if e['seq']<=seq and not ('Roaming Throne' in e['amp_present'] and states[e['seq']].get('chosen_throne') in ('Human','Goblin')))
   natural_equiv=ordinary+sum((n+1)//2 for n in doubled.values())
   necessary=(label=='basic' and natural_equiv<2) or (label=='strong' and snap['ggs_dragons']>=3 and natural_equiv<3 and snap['evasive_power']-(len([e for e in births if e['seq']<=seq])-natural_equiv)*5<15)
   if label=='basic' and necessary:
    # Basic has a two-own-turn window. Later independent connections within that window
    # support amplification, rather than necessity merely for the earliest observed state.
    later_groups=collections.Counter((e['global_turn'],states[e['seq']]['combat_ordinal']) for e in births if e['turn']<=d1+2 and 'Roaming Throne' in e['amp_present'] and states[e['seq']].get('chosen_throne') in ('Human','Goblin'))
    later_ordinary=sum(1 for e in births if e['turn']<=d1+2 and not ('Roaming Throne' in e['amp_present'] and states[e['seq']].get('chosen_throne') in ('Human','Goblin')))
    if later_ordinary+sum((n+1)//2 for n in later_groups.values())>=2:necessary=False

   return {'class':'AMPLIFIER-DEPENDENT' if necessary else 'AMPLIFIED GGS','material_amplifiers':material,'confidence':'observational direct trigger contribution','dependency_uncertain':not necessary}
  if label=='threat' and set(material)<= {'Purphoros, God of the Forge','Dragon Tempest'} and snap['observed_combat_damage']<15 and snap.get('unblocked_power',0)<20:
   direct=sum(a.get('amount',0) for a in contributions if a['kind']=='damage' and a['global_turn']==snap['global_turn'])
   if snap['observed_total_damage']-direct<20:return {'class':'AMPLIFIER-DEPENDENT','material_amplifiers':material,'confidence':'direct amplifier damage necessary for observed damage threshold'}
  return {'class':'AMPLIFIED GGS','material_amplifiers':material,'confidence':'contribution observed; necessity not established','dependency_uncertain':True}
 for label in ['basic','strong','threat']:metrics[label+'_dependency']=dependency(label)
 factory_turns=collections.defaultdict(set);metrics['renewable_ammunition_confirmed_turn']=None
 for ev in events:
  if ev['kind']=='factory_ammunition':
   factory_turns[ev['source']].add(ev['turn'])
   if len(factory_turns[ev['source']])>=2 and metrics['renewable_ammunition_confirmed_turn'] is None:metrics['renewable_ammunition_confirmed_turn']=ev['turn']
 metrics['factory_ammunition_events']=[e for e in events if e['kind']=='factory_ammunition']
 metrics['within_one']=bool(len(births)>1 and metrics['dragon_1_to_2_turns']<=1);metrics['within_two']=bool(len(births)>1 and metrics['dragon_1_to_2_turns']<=2)
 metrics['wipe_events']=wipe_events;metrics['recovery_definition']='Within three following Pure turns: another GGS-created Dragon and >=half pre-disruption offensive power (minimum5); only traced spell/ability mass loss >=3 creatures, combat casualties excluded';metrics['ggs_disruptions']=removed_ggs;metrics['interactions']=interaction;metrics['incoming_combat']=incoming;metrics['amp_events']=amp_events
 for w in wipe_events:
  w['recovered']=any(s['turn']<=w['turn']+3 and s['seq']>w['seq'] and s['ggs_total']>w['ggs_total'] and s['offensive_power']>=max(5,w['power_before']/2) for s in states)
 metrics['final_pure_turn']=turncount
 # Primary failure classification is provisional until representative logs are audited.
 reason=None
 if not metrics['win'] and metrics['threat_turn']:
  t=metrics['threat_turn'];sources={a.get('source_id') for a in incoming if a['turn']>=t and a.get('source_id') is not None}
  sources|={int(re.search(r'Ai\((\d+)\)',a['who']).group(1))-1 for a in interaction if a['turn']>=t}
  if len(sources)>=2:reason=9
  else:reason=8
 elif metrics['basic_turn'] is None:
  if any(not w['recovered'] and (not births or first['seq']<=w['seq'] and w['turn']<=d1+2) for w in wipe_events):reason=6
  elif any(not d.get('voluntary_reload') and (not births or first['seq']<=d['seq'] and d['turn']<=d1+2) for d in removed_ggs):reason=5
  elif not births and (not casts or max((s['mana_sources'] for s in states),default=0)<3):reason=1
  elif births:
   last=states[-1]
   post=[s for s in states if metrics['first_dragon_turn']<s['turn']<=metrics['first_dragon_turn']+2 and s['active']]
   if not post:reason=8
   elif not any(s['fresh_attacking_count'] or (s['phase']=='COMBAT_BEGIN' or s['phase']=='COMBAT_DECLARE_ATTACKERS' and s['attacker_count']==0) and s['fresh_creatures'] for s in post):reason=2
   elif not any(s['fresh_attacking_count'] or (s['phase']=='COMBAT_BEGIN' or s['phase']=='COMBAT_DECLARE_ATTACKERS' and s['attacker_count']==0) and s['fresh_ready'] for s in post):reason=4
   elif not any(s['fresh_unblocked_power'] for s in post if s['phase'].startswith('COMBAT')):reason=3
   elif len(births)>=2:reason=7
   else:reason=4
  elif max((s['fresh_creatures'] for s in states),default=0)==0:reason=2
  else:reason=3
 elif not metrics['threat_turn']:reason=8 if metrics['strong_turn'] and not metrics['win'] else 7
 elif not metrics['win']:reason=8
 metrics['primary_stall_category']=reason
 # Definite repeated self-sabotage: commander clamped to death, or offensive ninjutsu removes it with no replacement engine.
 if 'Skullclamp targeting [Goro-Goro and Satoru' in log:metrics['artifact_reasons'].append('Commander targeted by Skullclamp; requires audit, not automatic failure')
 metrics['mulligans']={}
 for who,n,redo in re.findall(r'DragonMind CasualSeven: player=(Ai\(\d+\)-.+?) reshuffles=(\d+) redraw=(true|false)',(directory/row['log']).read_text(errors='replace')):
  if redo=='false':metrics['mulligans'][who]=int(n)
 metrics['pure_mulligans']=metrics['mulligans'].get(name)
 metrics['provisional']=True
 metrics['snapshot_life_match_rate']=sum(s['life_match'] for s in states)/len(states) if states else None
 return metrics,{'states':states,'events':events,'personal_turn_map':pureturns}

def run(directory):
 directory=Path(directory);out=directory/'analysis';out.mkdir(exist_ok=True)
 result=[]
 for row in json.loads((directory/'summary.json').read_text()):
  if row['status']!='completed':result.append(row);continue
  m,t=extract(directory,row);result.append(m);(out/f"{row['seed']}-r{row['seat_rotation']}.json").write_text(json.dumps(t,separators=(',',':')))
 (out/'games.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps([{'seed':m['seed'],'rotation':m.get('rotation'),'d1':m.get('first_dragon_turn'),'d2':m.get('second_dragon_turn'),'basic':m.get('basic_turn'),'strong':m.get('strong_turn'),'threat':m.get('threat_turn'),'peak':m.get('peak_simultaneous_ggs_dragons'),'gaps':m.get('measurement_gaps'),'stall':m.get('primary_stall_category')} for m in result],indent=2))
if __name__=='__main__':run(sys.argv[1])
