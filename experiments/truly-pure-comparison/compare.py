"""Paired seed-block statistics; conditional rates retain explicit denominators."""
import argparse,collections,json,statistics
from pathlib import Path
import numpy as np
ARMS=['Pure_GGS','Truly_Pure_GGS_v2']
def wilson(k,n):
 if not n:return None
 z=1.95996398454;p=k/n;d=1+z*z/n;h=z*((p*(1-p)/n+z*z/(4*n*n))**.5)/d;c=(p+z*z/(2*n))/d;return [c-h,c+h]
def timing(v):
 v=[x for x in v if x is not None];return {'n':len(v),'mean':statistics.mean(v) if v else None,'median':statistics.median(v) if v else None}
def yes(m,k):return bool(m.get(k))
def summarize(games):
 n=len(games);ignited=[m for m in games if m['first_dragon_turn'] is not None]
 metrics={}
 for name,k in [('ignition','first_dragon_turn'),('basic','basic_turn'),('strong','strong_turn'),('threat','threat_turn'),('strict_dragon_pressure','strict_dragon_threat_turn'),('win','win')]:
  numerator=sum(yes(m,k) for m in games);metrics[name]={'k':numerator,'n':n,'rate':numerator/n if n else None,'wilson95':wilson(numerator,n)}
  if name not in ('ignition','win'):
   numerator=sum(yes(m,k) for m in ignited);metrics[name+'_conditional_ignited']={'k':numerator,'n':len(ignited),'rate':numerator/len(ignited) if ignited else None,'wilson95':wilson(numerator,len(ignited))}
 for name in ('within_one','within_two'):
  k=sum(m[name] for m in ignited);metrics[name]={'k':k,'n':len(ignited),'rate':k/len(ignited) if ignited else None,'wilson95':wilson(k,len(ignited))}
 threats=[e for m in games for e in m['protection_threats']];d=[e for m in games for e in m['disruptions'] if not e['voluntary_or_protective_bounce']]
 recovery_eligible=[e for e in d if e['three_turn_followup_available'] or e['restarted_within_three']]
 metrics.update({'timing':{key:timing(m.get(key) for m in games) for key in ['ggs_cast_turn','ready_ignition_opportunity_turn','first_dragon_turn','second_dragon_turn','access_turn','reliable_access_confirmed_turn','renewable_ammunition_turn','renewable_ammunition_confirmed_turn','usable_renewable_ammunition_confirmed_turn','momentum_established_turn','strong_turn','threat_turn','strict_dragon_threat_turn']},'mulligans':timing(m['pure_mulligans'] for m in games),'disruptions':len(d),'games_disrupted':sum(any(not d['voluntary_or_protective_bounce'] for d in m['disruptions']) for m in games),'disruption_types':dict(collections.Counter(e['type'] for e in d)),'redeployment_downtime':timing(e['downtime_turns'] for e in d),'restart_anytime':{'k':sum(e['restart_observed'] for e in d),'n':len(d)},'restart_within_three_all':{'k':sum(e['restarted_within_three'] for e in d),'n':len(d)},'restart_within_three_with_followup':{'k':sum(e['restarted_within_three'] for e in recovery_eligible),'n':len(recovery_eligible)},'recovery_censored':len(d)-len(recovery_eligible),'observed_protection_responses':sum(bool(e['responses']) for e in threats),'responses_with_preservation':sum(e.get('protection_with_preservation',False) for e in threats),'targeted_or_wipe_threats_logged':len(threats),'candidate_protection_visible':sum(bool(e['protection_candidates']) for e in threats),'combat_uptime':{'present':sum(m['commander_combat_turns_present'] for m in games),'observed':sum(m['observed_combat_turns'] for m in games)},'post_cast_combat_uptime':{'present':sum(m['commander_post_cast_combat_turns_present'] for m in games),'observed':sum(m['observed_post_cast_combat_turns'] for m in games)},'static_protection_games':sum(bool(m['static_protected_combat_turns']) for m in games),'wipe_recovery':{'k':sum(w['recovered'] for m in games for w in m['wipe_events']),'n':sum(len(m['wipe_events']) for m in games)},'bottlenecks':dict(collections.Counter(m['primary_bottleneck'] for m in games if m['primary_bottleneck'])),'loss_contexts':dict(collections.Counter(m['failure_context'] for m in games if m['failure_context'])),'blocked_fresh_games':sum(bool(m['blocked_fresh_combats']) for m in games),'blocked_fresh_combats':sum(len(m['blocked_fresh_combats']) for m in games),'potentially_affordable_cadence_games_screen':sum(any(w['potentially_affordable_screen'] for w in m['blocked_fresh_combats']) for m in games),'feedback_sources':dict(collections.Counter(c for m in games for c in m['feedback_sources'])),'student_copies':dict(collections.Counter(e['copied_name'] for m in games for e in m['student_copies']))})
 metrics['cards']={}
 for c in sorted({c for m in games for c in m['cards']}):
  entries=[m['cards'].get(c,{}) for m in games]
  metrics['cards'][c]={'exposed_games':sum(e.get('hand_seen',False) or e.get('battlefield_seen',False) for e in entries),'battlefield_games':sum(e.get('battlefield_seen',False) for e in entries),'cast_games':sum(e.get('casts',0)>0 for e in entries),'casts':sum(e.get('casts',0) for e in entries),'actions':sum(e.get('actions',0) for e in entries),'observed_cards':sum(e.get('cards_drawn_observed',0) for e in entries),'observed_treasures':sum(e.get('treasures_created_observed',0) for e in entries),'unconverted_hand_exposure_3_turns':sum(e.get('hand_seen',False) and not e.get('battlefield_seen',False) and not e.get('casts',0) and m['final_pure_turn']-e['first_hand_turn']>=3 for m,e in zip(games,entries) if e.get('first_hand_turn') is not None)}
 return metrics
def comparison(games):
 grouped={arm:[m for m in games if m['variant']==arm] for arm in ARMS};keys={arm:{(m['seed'],m['rotation']):m for m in ms} for arm,ms in grouped.items()};assert set(keys[ARMS[0]])==set(keys[ARMS[1]])
 seeds=sorted({s for s,r in keys[ARMS[0]]});assert all((s,r) in keys[ARMS[0]] for s in seeds for r in range(4));rng=np.random.default_rng(202610209);indices=rng.integers(0,len(seeds),(4000,len(seeds)));effects={}
 for name,k in [('ignition','first_dragon_turn'),('basic','basic_turn'),('strong','strong_turn'),('threat','threat_turn'),('strict_dragon_pressure','strict_dragon_threat_turn'),('win','win')]:
  block=np.array([sum(yes(keys[ARMS[1]][s,r],k)-yes(keys[ARMS[0]][s,r],k) for r in range(4))/4 for s in seeds]);boot=block[indices].mean(axis=1);effects[name]={'experimental_minus_control_pp':float(block.mean()*100),'paired_seed_bootstrap95_pp':[float(x) for x in np.quantile(boot,[.025,.975])*100]}
 return {'valid_games':len(games),'seed_blocks':len(seeds),'arms':{a:summarize(grouped[a]) for a in ARMS},'paired_effects':effects,'uncertainty':'Intervals quantify seed variation under this engine/pilot; not AI bias. Timing and post-disruption conditional groups differ between decks. Individual changed-card causal effects are not isolated.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batches',nargs='+',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();games=[]
 for directory in a.batches:
  for row in json.loads((directory/'summary.json').read_text()):
   assert row['status']=='completed';key=f"{row['variant']}-{row['seed']}-r{row['seat_rotation']}";m=json.loads((directory/'analysis'/(key+'-extended.json')).read_text());m['batch_directory']=str(directory.resolve());games.append(m)
 result=comparison(games);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'valid':len(games),'effects':result['paired_effects']}))
