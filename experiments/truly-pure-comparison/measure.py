"""Conservative supplementary observations; projections are labelled, never game outcomes."""
import collections,gzip,json,re
from pathlib import Path
GGS='Goro-Goro and Satoru'
PROTECTION={'An Offer You Can\'t Refuse','Swan Song','Mana Drain','Fierce Guardianship','Deflecting Swat','March of Swirling Mist','Malakir Rebirth','Siren Stormtamer','Spellskite','Dour Port-Mage'}
STATIC={'Lightning Greaves','Swiftfoot Boots'}
DRAW={'Ingenious Infiltrator','Dour Port-Mage','Enduring Curiosity','Grazilaxx, Illithid Scholar','Satoru, the Infiltrator',"Yuriko, the Tiger's Shadow",'Mystic Remora','Skullclamp','Frostcliff Siege','Kaito, Cunning Infiltrator'}
TREASURE={'Ragavan, Nimble Pilferer','Prosperous Thief','Professional Face-Breaker','Grim Hireling','Orochi Soul-Reaver','Goldspan Dragon'}
MASS={'Toxic Deluge','Blasphemous Act','Cyclonic Rift','Damnation','Wrath of God','Vanquish the Horde','Farewell','Game Over','Living Death','Fumigate','Austere Command','Blasphemous Edict','Dusk','Fell the Mighty'}
ROCKS={'Sol Ring':2,'Arcane Signet':1,'Fellwar Stone':1,'Talisman of Creativity':1,'Talisman of Dominance':1,'Talisman of Indulgence':1}
def mana_bound(p):
 return sum((1 if 'Land' in c.get('type','') else ROCKS.get(c['name'],1 if c['name']=='Treasure Token' else 0)) for c in p['battlefield'] if not c.get('tapped') and not c.get('phased_out'))
def extract(directory,row,m,t):
 directory=Path(directory);idx=row['seats'].index(row['variant']);path=directory/'audit'/Path(row['log']).stem/f'seat-{idx}.jsonl.gz';turnmap={int(k):v for k,v in t['personal_turn_map'].items()}
 result={'protection_availability_fidelity':'Candidate cards visible at threat; exact legal castability, floating mana, and target legality not logged. Untapped-source budget is a screen only.','war_counterfactual_fidelity':'Observed blocked fresh combat, public untapped-source budget screen; no causal War Cadence ablation, opponent floating mana and choices unknown.','cards':{},'resource_events':[],'protection_threats':[],'disruptions':[],'blocked_fresh_combats':[],'ready_ignition_opportunity_turn':None,'engine_exhaustion_turns':[],'strict_dragon_threat_turn':None,'peak_ready_ggs_dragon_power':0}
 cards=collections.defaultdict(lambda:{'hand_seen':False,'battlefield_seen':False,'casts':0,'actions':0,'cards_drawn_observed':0,'treasures_created_observed':0,'first_hand_turn':None,'first_battlefield_turn':None,'last_hand_turn':None,'final_in_hand':False})
 prev=None;lasttop={};states=[];seen_resource_ids=set();pending={};combat_windows={};sources={};first_hand=None;ggs_cast_events=[];seq=-1;student_ids=set();student_copies={};student_forms={};static_protected_turns=set();usable_factory_events={};held_back={};command_casts=[]
 with gzip.open(path,'rt') as f:
  for l in f:
   x=json.loads(l);s=x.get('state')
   if not s:continue
   p=next((p for p in s['players'] if p['id']==idx),None)
   if not p:continue
   seq+=1;turn=t['states'][seq]['turn'];brief=t['states'][seq];assert brief['global_turn']==s['turn']
   bf={c['id']:c for c in p['battlefield']};ggs=next((c for c in bf.values() if c['name']==GGS and c.get('commander')),None);ownstack=[c for c in s['stack'] if c.get('controller_id')==idx]
   for zone in ('hand','battlefield'):
    for c in p[zone]:
     e=cards[c['name']];e[zone+'_seen']=True
     if e['first_'+zone+'_turn'] is None:e['first_'+zone+'_turn']=turn
     if zone=='hand':e['last_hand_turn']=turn
     if c['name']=="Sakashima's Student":student_ids.add(c['id'])
   for c in bf.values():
    if c['id'] in student_ids and c['name']!="Sakashima's Student" and student_forms.get(c['id'])!=c['name']:student_copies[(seq,c['id'])]={'turn':turn,'global_turn':s['turn'],'seq':seq,'card_id':c['id'],'copied_name':c['name'],'power':c['power'],'keywords':c['keywords'],'commander':c.get('commander',False)}
   student_forms={c['id']:c['name'] for c in bf.values() if c['id'] in student_ids}
   if first_hand is None and p.get('hand'):
    first_hand=[c['name'] for c in p['hand']];result['keep_effective_land_faces']=sum('Land' in c.get('type','') or c['name'] in {'Malakir Rebirth','Fell the Profane','Sink into Stupor'} for c in p['hand']);result['keep_sol_ring']='Sol Ring' in first_hand;result['keep_quality_definition']='Observed random-seven effective land-face count and Sol Ring; no aggressive hand sculpting or inferred perfect color availability.'
   if prev:
    if any(c['name']==GGS and c.get('commander') for c in prev['p']['command']):
     for spell in ownstack:
      if spell['name']==GGS and spell.get('commander') and any(c['id']==spell['id'] for c in prev['p']['command']) and not any(c['id']==spell['id'] for c in p['command']):command_casts.append({'turn':turn,'global_turn':s['turn'],'seq':seq,'commander_id':spell['id']})
    gain=p['hand_count']-prev['p']['hand_count'];source=lasttop.get('name');own=lasttop.get('controller_id')==idx
    if gain>0 and own and source in DRAW and 'draw' in lasttop.get('description','').lower():
     result['resource_events'].append({'turn':turn,'global_turn':s['turn'],'seq':seq,'source':source,'kind':'observed_hand_gain','amount':gain});cards[source]['cards_drawn_observed']+=gain
    newtreasure=[c for c in bf.values() if c['name']=='Treasure Token' and c['id'] not in seen_resource_ids];seen_resource_ids.update(c['id'] for c in newtreasure)
    if newtreasure and own and source in TREASURE:
     result['resource_events'].append({'turn':turn,'global_turn':s['turn'],'seq':seq,'source':source,'kind':'observed_treasure_creation','amount':len(newtreasure)});cards[source]['treasures_created_observed']+=len(newtreasure)
    oldggs=prev['ggs']
    if oldggs and not ggs and not oldggs.get('phased_out'):
     dest=next((z for z in ('command','hand','graveyard','exile') if any(c['id']==oldggs['id'] for c in p[z])),None)
     voluntary=source in {'Alora, Merry Thief','Grazilaxx, Illithid Scholar','Dour Port-Mage'} and own
     kind='bounce' if dest=='hand' else 'exile' if dest=='exile' else 'removal'
     if source in MASS:kind='wipe'
     result['disruptions'].append({'turn':turn,'global_turn':s['turn'],'seq':seq,'source':source,'source_player_id':lasttop.get('controller_id'),'type':kind,'destination':dest,'voluntary_or_protective_bounce':voluntary,'ggs_total_before':brief['ggs_total'],'protection_candidates_before':sorted(PROTECTION & {c['name'] for c in prev['p']['hand']+prev['p']['battlefield']}),'untapped_budget_before':mana_bound(prev['p'])})
   # Observe opponent effects targeting the actual commander, plus known wipes.
   for c in s['stack']:
    if c.get('controller_id')==idx:continue
    desc=c.get('description','');spell_ggs=next((q for q in ownstack if q['name']==GGS and q.get('commander')),None);subject=ggs or spell_ggs;targeted=subject and re.search(r'\('+str(subject['id'])+r'\)',desc)
    if not targeted and not (ggs and (c['name'] in MASS or 'destroy all creatures' in desc.lower())):continue
    key=(s['turn'],c['id'],desc)
    if key not in pending:
     candidates=sorted(PROTECTION & {c['name'] for c in p['hand']+p['battlefield']})
     pending[key]={'turn':turn,'global_turn':s['turn'],'seq':seq,'source':c['name'],'description':desc,'ggs_id':subject['id'],'commander_on_stack':bool(spell_ggs and not ggs),'protection_candidates':candidates,'untapped_budget_screen':mana_bound(p),'responses':[],'resolved_observation':False}
    e=pending[key];e['responses']=sorted(set(e['responses'])|{q['name'] for q in ownstack if q['name'] in PROTECTION})
   if not s['stack']:
    for key,e in list(pending.items()):
     saved_hand='Dour Port-Mage' in e['responses'] and any(c['id']==e['ggs_id'] for c in p['hand'])
     e.update(resolved_observation=True,commander_preserved=bool(ggs),commander_saved_to_hand=bool(saved_hand),commander_phased_out=bool(ggs and ggs.get('phased_out')),protection_with_preservation=bool(e['responses'] and ggs),successful_response_avoided_loss=bool(e['responses'] and (ggs or saved_hand)));result['protection_threats'].append(e)
     if e['commander_on_stack'] and not ggs:result['disruptions'].append({'turn':e['turn'],'global_turn':e['global_turn'],'seq':e['seq'],'source':e['source'],'type':'counter','voluntary_or_protective_bounce':False,'ggs_total_before':brief['ggs_total'],'protection_candidates_before':e['protection_candidates'],'untapped_budget_before':e['untapped_budget_screen']})
     del pending[key]
   if s['active_player_id']==idx:
    if s['phase']=='COMBAT_BEGIN' and ggs and any(k in ggs['keywords'] for k in ('Hexproof','Shroud')):static_protected_turns.add(turn)
    if brief['phase']=='COMBAT_BEGIN' and ggs and brief['fresh_ready']>0 and result['ready_ignition_opportunity_turn'] is None:result['ready_ignition_opportunity_turn']=turn
    if brief['phase']=='END_OF_TURN' and p['hand_count']<=1 and not brief['factories'] and not brief['fresh_ready']:result['engine_exhaustion_turns'].append(turn)
    if brief['phase'].startswith('COMBAT'):
     key=(s['turn'],brief['combat_ordinal']);w=combat_windows.setdefault(key,{'turn':turn,'global_turn':s['turn'],'combat_ordinal':brief['combat_ordinal'],'ggs_present':False,'fresh_blocked':[],'fresh_unblocked':False,'own_budget_begin':None,'defender_budgets':{},'own_hand_begin':[]})
     w['actual_attack_declared']=w.get('actual_attack_declared',False) or brief['attacker_count']>0
     w['combat_end_observed']=w.get('combat_end_observed',False) or brief['phase']=='COMBAT_END'
     w['ggs_present']|=bool(ggs and not ggs.get('phased_out'))
     if brief['phase']=='COMBAT_BEGIN' and w['own_budget_begin'] is None:w['own_budget_begin']=mana_bound(p);w['own_hand_begin']=[c['name'] for c in p['hand']]
     if brief['phase']=='COMBAT_DECLARE_ATTACKERS' and ggs and brief['fresh_ready']>0 and brief['attacker_count']==0:
      blockers=[q for q in s['players'] if q['id']!=idx and any('Creature' in c.get('type','') and not c['tapped'] and not c.get('phased_out') for c in q['battlefield'])]
      if blockers:held_back[key]={'turn':turn,'global_turn':s['turn'],'fresh_ready':brief['fresh_ready'],'opponents_with_untapped_creatures':len(blockers),'uncertainty':'No recorded actual attack; public blocker presence does not establish legal blockage or explain AI choice. Review as possible access/AI artifact, not a proven access failure.'}
     if brief['phase'] in ('COMBAT_DECLARE_BLOCKERS','COMBAT_FIRST_STRIKE_DAMAGE','COMBAT_DAMAGE','COMBAT_END'):
      for a in s.get('combat',{}).get('attackers',[]):
       c=bf.get(a['attacker_id'])
       if not c or not c['entered_this_turn'] or c['power']<=0 or a.get('defender_kind')!='player':continue
       factory=next((e for e in t['events'] if e['kind']=='factory_ammunition' and e['id']==c['id'] and e['global_turn']==s['turn']),None)
       if factory:usable_factory_events[(c['id'],s['turn'])]={'source':factory['source'],'turn':turn,'global_turn':s['turn'],'name':c['name'],'fresh_attacking':True,'unblocked_observed':bool(a.get('unblocked')) or usable_factory_events.get((c['id'],s['turn']),{}).get('unblocked_observed',False)}
       if a.get('unblocked'):w['fresh_unblocked']=True
       if a.get('blocked'):
        defender=next((q for q in s['players'] if q['id']==a['defender_id']),None)
        if defender:w['defender_budgets'][a['defender_id']]=max(w['defender_budgets'].get(a['defender_id'],0),mana_bound(defender))
        item={'id':c['id'],'name':c['name'],'power':c['power'],'defender_id':a['defender_id'],'blockers':a['blocker_ids']}
        if item not in w['fresh_blocked']:w['fresh_blocked'].append(item)
   born_ids={e['id'] for e in t['events'] if e['kind']=='ggs_dragon' and e['seq']<=seq};attackers={a['attacker_id'] for a in s.get('combat',{}).get('attackers',[])}
   dragon_power=sum(max(0,c['power']) for c in bf.values() if c['id'] in born_ids and 'Flying' in c['keywords'] and not c.get('phased_out') and (c['id'] in attackers or (not c['tapped'] and (not c['summoning_sick'] or 'Haste' in c['keywords']))))
   result['peak_ready_ggs_dragon_power']=max(result['peak_ready_ggs_dragon_power'],dragon_power)
   if dragon_power>=20 and result['strict_dragon_threat_turn'] is None:result['strict_dragon_threat_turn']=turn
   states.append({'seq':seq,'turn':turn,'global_turn':s['turn'],'phase':s['phase'],'active':s['active_player_id']==idx,'ggs':bool(ggs and not ggs.get('phased_out')),'ggs_id':ggs['id'] if ggs else None,'hand_count':p['hand_count'],'bf':bf,'untapped_budget':mana_bound(p),'own_stack':ownstack})
   prev={'p':p,'ggs':ggs};lasttop=s['stack'][0] if s['stack'] else {}
 for e in pending.values():result['protection_threats'].append(e)
 for w in combat_windows.values():
  if not w['ggs_present'] or not w['fresh_blocked'] or w['fresh_unblocked']:continue
  if any(e['kind']=='ggs_dragon' and e['global_turn']==w['global_turn'] and t['states'][e['seq']]['combat_ordinal']==w['combat_ordinal'] for e in t['events']):continue
  w['tax_cost_screen']=min((w['defender_budgets'].get(a['defender_id'],0)+2 for a in w['fresh_blocked']),default=None)
  w['potentially_affordable_screen']=w['own_budget_begin'] is not None and w['own_budget_begin']>=w['tax_cost_screen']
  w['red_mana_and_float_unknown']=True;result['blocked_fresh_combats'].append(w)
 log=(directory/row.get('engine_transcript',row['log'])).read_text();personal=0;globalturn=0;cast_lines=[];action_lines=[];name=f'Ai({idx+1})-{row["variant"]}'
 dragon_damage_turns=collections.Counter();all_born_ids={e['id'] for e in t['events'] if e['kind']=='ggs_dragon'}
 for i,line in enumerate(log.splitlines(),1):
  mt=re.match(r'Turn: Turn (\d+)',line)
  if mt:globalturn=int(mt[1]);personal=turnmap.get(globalturn,personal)
  mt=re.match(r'Add To Stack: '+re.escape(name)+r' (cast|activated|triggered) (.+)',line)
  if mt:
   kind,desc=mt.groups();source=next((c for c in sorted(cards,key=len,reverse=True) if desc==c or desc.startswith(c+' ') or desc.startswith(c+' -')),None)
   if source:cards[source]['casts' if kind=='cast' else 'actions']+=1
   if kind!='triggered':action_lines.append({'turn':personal,'global_turn':globalturn,'line':i,'kind':kind,'description':desc,'source':source,'category':'protection' if source in PROTECTION else 'ggs_development_or_haste' if source==GGS else 'ninjutsu_candidate' if kind=='activated' and source in {"Sakashima's Student",'Ingenious Infiltrator','Thousand-Faced Shadow','Prosperous Thief','Orochi Soul-Reaver','Fallen Shinobi',"Yuriko, the Tiger's Shadow",'Higure, the Still Wind','Satoru Umezawa'} else 'development_or_other'})
   if kind=='cast':cast_lines.append({'turn':personal,'global_turn':globalturn,'line':i,'card':desc})
   if kind=='cast' and desc==GGS:ggs_cast_events.append({'turn':personal,'global_turn':globalturn,'line':i})
  damage=re.match(r'Damage: .+ \((\d+)\) deals (\d+) combat damage to (Ai\(\d+\)-.+?)\.',line)
  if damage and int(damage[1]) in all_born_ids and damage[3]!=name and globalturn in turnmap:dragon_damage_turns[personal]+=int(damage[2])
 result['ggs_dragon_combat_damage_each_turn']=dict(dragon_damage_turns)
 hits=[turn for turn,damage in dragon_damage_turns.items() if damage>=15]
 if hits:result['strict_dragon_threat_turn']=min([result['strict_dragon_threat_turn']] + hits) if result['strict_dragon_threat_turn'] is not None else min(hits)
 for c in prev['p']['hand'] if prev else []:cards[c['name']]['final_in_hand']=True
 for e in result['disruptions']:
  later=[s for s in states if s['seq']>e['seq']];reentry=next((s for s in later if s['ggs']),None)
  postloss=next((b for b in t['events'] if b['kind']=='ggs_dragon' and b['seq']>e['seq']),None)
  # A trigger pending when the commander left can still resolve and create a
  # Dragon. That is valid production, but it does not establish engine restart.
  nextdragon=next((b for b in t['events'] if b['kind']=='ggs_dragon' and reentry is not None and b['seq']>reentry['seq']),None)
  e['first_post_loss_creation_turn']=postloss['turn'] if postloss else None
  e['creation_before_reentry_observed']=bool(postloss and (reentry is None or postloss['seq']<reentry['seq']))
  e['restart_definition']='Observed GGS reentry followed by a GGS-created Dragon; pre-reentry pending-trigger production excluded.'
  e.update(reentry_turn=reentry['turn'] if reentry else None,downtime_turns=reentry['turn']-e['turn'] if reentry else None,next_trigger_turn=nextdragon['turn'] if nextdragon else None,restarted_within_three=bool(nextdragon and nextdragon['turn']<=e['turn']+3),restart_observed=bool(nextdragon),three_turn_followup_available=m['final_pure_turn']>=e['turn']+3)
  missed={s['turn'] for s in later if s['active'] and s['phase']=='COMBAT_BEGIN' and not s['ggs'] and (reentry is None or s['seq']<reentry['seq'])};e['observed_own_combat_turns_missed_before_reentry']=len(missed)
 for e in result['protection_threats']:
  nextdragon=next((b for b in t['events'] if b['kind']=='ggs_dragon' and b['seq']>e['seq']),None);e['another_dragon_within_three_after_response']=bool(e.get('successful_response_avoided_loss') and nextdragon and nextdragon['turn']<=e['turn']+3)
 combat_uptime={}
 for s in states:
  if s['active'] and s['phase']=='COMBAT_BEGIN':combat_uptime[s['global_turn']]=combat_uptime.get(s['global_turn'],False) or s['ggs']
 result['commander_observed_active_phase_uptime']=sum(combat_uptime.values())/max(1,len(combat_uptime));result['commander_combat_turns_present']=sum(combat_uptime.values());result['observed_combat_turns']=len(combat_uptime)
 post_cast_uptime={g:v for g,v in combat_uptime.items() if m['ggs_cast_turn'] is not None and turnmap[g]>=m['ggs_cast_turn']};result['commander_post_cast_combat_turns_present']=sum(post_cast_uptime.values());result['observed_post_cast_combat_turns']=len(post_cast_uptime)
 result['initial_keep_observed']=first_hand;result['ggs_cast_events']=ggs_cast_events;result['cards']=dict(cards);result['cast_events']=cast_lines;result['student_copies']=list(student_copies.values());result['static_protected_combat_turns']=sorted(static_protected_turns);result['observed_command_zone_casts']=command_casts;result['tax_fidelity']='Command-to-stack transitions observed; exact mana payments and cost modifiers are not logged. Recasts from hand are distinct from observed command-zone casts.'
 for w in result['blocked_fresh_combats']:
  w['same_turn_actual_spells']=[c for c in cast_lines if c['global_turn']==w['global_turn']];w['same_turn_actions']=[c for c in action_lines if c['global_turn']==w['global_turn']];w['mana_spent_exact_unknown']=True
 result['momentum_established_turn']=min((e['turn'] for e in result['resource_events']),default=None)
 result['usable_factory_ammunition_events']=list(usable_factory_events.values());factory_turns=collections.defaultdict(set);result['usable_renewable_ammunition_confirmed_turn']=None
 result['held_back_fresh_combat_candidates']=[v for k,v in held_back.items() if not combat_windows[k]['actual_attack_declared'] and combat_windows[k]['combat_end_observed']]
 for e in result['usable_factory_ammunition_events']:
  factory_turns[e['source']].add(e['turn'])
  if len(factory_turns[e['source']])>=2 and result['usable_renewable_ammunition_confirmed_turn'] is None:result['usable_renewable_ammunition_confirmed_turn']=e['turn']
 # Resource return followed by another actual GGS creation: a feedback association,
 # not proof that drawn cards or a particular Treasure paid for that creation.
 result['feedback_sources']=sorted({e['source'] for e in result['resource_events'] if any(b['kind']=='ggs_dragon' and b['seq']>e['seq'] and b['turn']<=e['turn']+2 for b in t['events'])})
 result['ready_ignition_opportunity_fidelity']='GGS and positive-power fresh attack-ready body observed at combat beginning; blocker/target legality unknown, so a candidate opportunity rather than proven viable connection.'
 result['primary_bottleneck']=None;result['failure_context']=None
 nonvoluntary=[d for d in result['disruptions'] if not d['voluntary_or_protective_bounce']]
 post=[s for s in t['states'] if s['active'] and (not m['first_dragon_turn'] or s['turn']>m['first_dragon_turn'])]
 if not m['win']:
  if m['threat_turn']:result['failure_context']='THREATENED_AND_FOCUSED' if m['primary_stall_category']==9 else 'OPPONENT_WON_AFTER_THREAT'
  elif any(not d['restarted_within_three'] for d in nonvoluntary) or any(not w['recovered'] for w in m['wipe_events']):result['primary_bottleneck']='PROTECTION/RECOVERY'
  elif not m['first_dragon_turn']:result['primary_bottleneck']='IGNITION' if m['ggs_cast_turn'] is None else 'ACCESS' if result['blocked_fresh_combats'] else 'AMMUNITION' if not any(s['fresh_ready'] for s in t['states'] if s['active']) else 'IGNITION'
  elif result['blocked_fresh_combats'] and not m['basic_turn']:result['primary_bottleneck']='ACCESS'
  elif not any(s['fresh_ready'] for s in post):result['primary_bottleneck']='AMMUNITION'
  elif result['engine_exhaustion_turns'] or (not m['basic_turn'] and m['primary_stall_category']==4):result['primary_bottleneck']='MOMENTUM'
  elif m['strong_turn']:result['failure_context']='OPPONENT_WON_BEFORE_PRESSURE_THRESHOLD'
  elif m['basic_turn'] and m['cumulative_dragons']>=3 and m['final_pure_turn']>=m['first_dragon_turn']+3:result['primary_bottleneck']='POWER/PAYOFF_CANDIDATE_REQUIRES_REVIEW'
  else:result['failure_context']='LIMITED_FOLLOWUP_OR_UNRESOLVED'
 result['classification_fidelity']='Conservative automated primary-bottleneck screen; power/payoff requires manual healthy-engine review, focused losses remain distinct, no attribution of every loss to a deck defect.'
 m.update(result);return m
