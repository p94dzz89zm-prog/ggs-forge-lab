"""Paired seed-cluster comparisons; positive effects favor retaining amplifier."""
import argparse,collections,csv,json,random,statistics,sys,subprocess
from pathlib import Path
from inspect_games import inspect
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots';P=json.loads((HERE/'protocol.json').read_text());cards=[a['removed'] for a in P['arms']]+[P['replacement']]
parser=argparse.ArgumentParser();parser.add_argument('--through-stage',type=int);args=parser.parse_args()
baseline=json.loads((WORK/'pure-ggs/Pure_GGS_Results.json').read_text())['games'];B={(m['seed'],m['rotation']):m for m in baseline}
cache=OUT/'baseline-exposure.json'
if cache.exists():E=json.loads(cache.read_text())
else:
 E={}
 for d in sorted((WORK/'pure-ggs').glob('batch-*')):
  for r in json.loads((d/'summary.json').read_text()):E[f"{r['seed']}-r{r['seat_rotation']}"]=inspect(d,r,cards)
 cache.write_text(json.dumps(E,indent=2)+'\n')
new=[];batches=[];failed_attempts=[]
for d in sorted(OUT.glob('stage-*')):
 if args.through_stage is not None and int(d.name.split('-')[1])>args.through_stage:continue
 if not (d/'performance.json').exists():continue
 batch=json.loads((d/'performance.json').read_text())
 if batch['valid']!=batch['requested']:continue
 batch['path']=str(d);batches.append(batch)
 failed_attempts.extend(json.loads((d/'failed-attempts.json').read_text()) if (d/'failed-attempts.json').exists() else [])
 rows=json.loads((d/'summary.json').read_text());receipt=d/'audit-integrity.json'
 if not receipt.exists() or json.loads(receipt.read_text())['finished_games']!=len(rows):subprocess.run([sys.executable,str(HERE/'audit_integrity.py'),str(d),'--repair','--prune-raw'],check=True)
 for r in rows:
  if r['status']!='completed':new.append(r);continue
  key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";m=json.loads((d/'analysis'/(key+'-metrics.json')).read_text());af=d/'analysis'/(key+'-inspection.json')
  if af.exists():i=json.loads(af.read_text())
  else:i=inspect(d,r,cards);af.write_text(json.dumps(i,indent=2)+'\n')
  m['inspection']=i;m['excluded']=bool(m['measurement_gaps']) or m['snapshot_life_match_rate']!=1.0 or not i['clamp_cleared'];new.append(m)
def rates(rs):
 ig=[r for r in rs if r.get('first_dragon_turn') is not None]
 return {'ignition':sum(r.get('first_dragon_turn') is not None for r in rs)/len(rs),**{k:sum(bool(r.get(k+'_turn')) for r in rs)/len(rs) for k in ['basic','strong','threat']},'win':sum(r['win'] for r in rs)/len(rs),**{k:sum(bool(r.get(k)) for r in ig)/len(ig) if ig else None for k in ['within_one','within_two']},**{k+'_conditional':sum(bool(r.get(k+'_turn')) for r in ig)/len(ig) if ig else None for k in ['basic','strong','threat']}}
def times(rs):
 return {k:{'n':len(x),'mean':statistics.mean(x) if x else None,'median':statistics.median(x) if x else None} for k in ['ggs_cast_turn','first_dragon_turn','second_dragon_turn','threat_turn'] for x in [[r[k] for r in rs if r.get(k) is not None]]}
def dependency_counts(rs):
 return {k:dict(collections.Counter((m.get(k+'_dependency') or {}).get('class') for m in rs if m.get(k+'_turn') is not None)) for k in ['basic','strong','threat']}
def recovery(rs):
 w=[e for r in rs for e in r.get('wipe_events',[])];return {'events':len(w),'recovered':sum(e['recovered'] for e in w)}
arms=[]
for arm in P['arms']:
 rs=sorted([m for m in new if m['variant']==arm['name'] and m['status']=='completed' and not m.get('excluded')],key=lambda m:(m['seed'],m['rotation']))
 if not rs:continue
 assert len({(m['seed'],m['rotation']) for m in rs})==len(rs)
 bs=[B[m['seed'],m['rotation']] for m in rs];b=rates(bs);v=rates(rs);groups=collections.defaultdict(list)
 for j,m in enumerate(rs):groups[m['seed']].append(j)
 rng=random.Random(20261007);keys=sorted(groups);samples=collections.defaultdict(list)
 for _ in range(4000):
  indices=[j for seed in rng.choices(keys,k=len(keys)) for j in groups[seed]];br=rates([bs[j] for j in indices]);vr=rates([rs[j] for j in indices])
  for k in b:
   if br[k] is not None and vr[k] is not None:samples[k].append((br[k]-vr[k])*100)
 def interval(k,q=(.025,.975)):
  s=sorted(samples[k]);return [round(s[min(int(len(s)*x),len(s)-1)],2) for x in q] if s else None
 contrasts={k:{'baseline_percent':round(b[k]*100,2) if b[k] is not None else None,'replacement_percent':round(v[k]*100,2) if v[k] is not None else None,'retention_effect_pp':round((b[k]-v[k])*100,2) if b[k] is not None and v[k] is not None else None,'paired_seed_bootstrap_95':interval(k)} for k in b};contrasts['threat']['six_comparison_interval']=interval('threat',(.0041667,.9958333))
 previous=next((n for n in reversed(P['stages']) if n<len(rs)),0);pr=rs[:previous];pb=bs[:previous];shifts={k:round(contrasts[k]['retention_effect_pp']-(rates(pb)[k]-rates(pr)[k])*100,2) for k in P['primary']} if previous else {}
 bt=times(bs);vt=times(rs);pt=times(pr);pbt=times(pb);time_shifts={k:((bt[k]['median']-vt[k]['median'])-(pbt[k]['median']-pt[k]['median'])) if all(x[k]['median'] is not None for x in [bt,vt,pt,pbt]) else None for k in bt}
 be=[E[f"{m['seed']}-r{m['rotation']}"] for m in rs];ve=[m['inspection'] for m in rs];card=arm['removed'];exposed=sum(x['cards'][card]['hand_seen'] or y['cards'][P['replacement']]['hand_seen'] for x,y in zip(be,ve))
 def usage(es,c):return {'hand_games':sum(e['cards'][c]['hand_seen'] for e in es),'cast_games':sum(e['cards'][c]['casts']>0 for e in es),'battlefield_games':sum(e['cards'][c]['battlefield_seen'] for e in es),'trigger_or_activation_games':sum(e['cards'][c]['activated_or_triggered']>0 for e in es)}
 stability={'n':len(rs),'previous':previous,'slot_exposed_pairs':exposed,'effect_shifts':shifts,'timing_effect_shifts':time_shifts,'passed':len(rs)>=64 and exposed>=20 and all(abs(x)<=10 for x in shifts.values()) and all(x is None or abs(x)<=1 for x in time_shifts.values())}
 arms.append({**arm,'valid':len(rs),'baseline_ignited':sum(x['first_dragon_turn'] is not None for x in bs),'replacement_ignited':sum(x['first_dragon_turn'] is not None for x in rs),'contrasts':contrasts,'baseline_timing':bt,'replacement_timing':vt,'baseline_usage':usage(be,card),'replacement_usage':usage(ve,P['replacement']),'baseline_material_thresholds':{k:sum(card in (m.get(k+'_dependency') or {}).get('material_amplifiers',[]) for m in bs) for k in ['basic','strong','threat']},'baseline_stalls':dict(collections.Counter(m['primary_stall_category'] for m in bs)),'replacement_stalls':dict(collections.Counter(m['primary_stall_category'] for m in rs)),'baseline_dependency_counts':dependency_counts(bs),'replacement_dependency_counts':dependency_counts(rs),'baseline_recovery':recovery(bs),'replacement_recovery':recovery(rs),'stability':stability})
result={'protocol':P,'attempted':len(new)+len(failed_attempts),'valid':sum(m['status']=='completed' and not m.get('excluded') for m in new),'excluded':[(m['variant'],m['seed'],m.get('rotation',m.get('seat_rotation')),m['status']) for m in new if m['status']!='completed' or m.get('excluded')],'batches':batches,'arms':arms,'games':new,'reused_baseline_games':baseline,'baseline_exposure':E,'limitations':['Entire card versus Whisper with other five amplifiers retained.','Common seeds do not guarantee identical trajectories or openings.','Conditional ignited rates select different games and are secondary.','Bootstrap intervals reflect seed variation, not pilot or model bias; repeated stages/multiple outcomes remain exploratory.','Presence or hand exposure, including tutored/stolen same-name cards, is not automatically material contribution.']}
result['failed_attempts']=failed_attempts
result['archive_integrity_exclusions']=sum(x.get('excluded_kind')=='incomplete_saved_audit' for x in failed_attempts)
result['measurement_integrity_exclusions']=sum(x.get('excluded_kind')=='phase_reconciliation' for x in failed_attempts)
copy_recovery=OUT/'archive-copy-recovery.json'
result['archive_copy_recovery']=json.loads(copy_recovery.read_text()) if copy_recovery.exists() else None
result['simulator_error_attempts']=len(result['excluded'])+sum(x.get('simulator_failure',x['original_record']['status']!='completed') for x in failed_attempts)
interruption=OUT/'execution-interruptions.json'
result['execution_interruptions']=json.loads(interruption.read_text()) if interruption.exists() else None
result['known_unavailable_completed_attempts']=(result['execution_interruptions'] or {}).get('known_completed_without_recoverable_logs',0)
result['known_attempted_total']=result['attempted']+result['known_unavailable_completed_attempts']
result['unresolved_exclusions']=list(result['excluded'])+[(x['original_record']['variant'],x['original_record']['seed'],x['original_record']['seat_rotation'],x['original_record']['status']) for x in failed_attempts if not x['resolved']]
result['resolved_exclusions']=[(x['original_record']['variant'],x['original_record']['seed'],x['original_record']['seat_rotation'],x['original_record']['status']) for x in failed_attempts if x['resolved']]
result['excluded']+=result['resolved_exclusions']
maps={a['name']:{(m['seed'],m['rotation']):m for m in new if m['variant']==a['name'] and m['status']=='completed' and not m.get('excluded')} for a in arms}
shared=set.intersection(*(set(x) for x in maps.values())) if maps else set();result['common_comparison_games_per_arm']=len(shared);rank_pairs=[]
for i,a in enumerate(arms if shared else []):
 for c in arms[i+1:]:
  groups=collections.defaultdict(list)
  for key in sorted(shared):groups[key[0]].append((bool(maps[c['name']][key]['threat_turn'])-bool(maps[a['name']][key]['threat_turn']))*100)
  keys=sorted(groups);rng=random.Random(20261008);boot=[]
  for _ in range(4000):
   values=[v for key in rng.choices(keys,k=len(keys)) for v in groups[key]];boot.append(statistics.mean(values))
  boot.sort();rank_pairs.append({'card_A':a['removed'],'card_B':c['removed'],'common_games':len(shared),'A_retention_over_B_pp':statistics.mean([v for values in groups.values() for v in values]),'paired_seed_bootstrap_95':[boot[int(len(boot)*q)] for q in (.025,.975)],'fifteen_comparison_interval':[boot[min(int(len(boot)*q),len(boot)-1)] for q in (.0016667,.9983333)]})
result['direct_threat_retention_rank_comparisons']=rank_pairs
(OUT/'Pure_GGS_Amplifier_Results.json').write_text(json.dumps(result,indent=2)+'\n')
fields=['variant','seed','rotation','status','excluded','excluded_kind','win','ggs_cast_turn','first_dragon_turn','second_dragon_turn','within_one','within_two','basic_turn','strong_turn','threat_turn','cumulative_dragons','peak_simultaneous_ggs_dragons','peak_offensive_power','dragon_damage','primary_stall_category','log','audit','first_fresh_connection','dragon_1_to_2_turns','multi_dragon_turn','dragons_each_turn','peak_evasive_power','renewable_ammunition_turn','renewable_ammunition_confirmed_turn','access_turn','reliable_access_confirmed_turn','card_acceleration_turn','mana_acceleration_turn','pure_mulligans','engine_seconds','final_global_turn','final_pure_turn','basic_dependency','strong_dependency','threat_dependency','interactions','ggs_disruptions','wipe_events']
with (OUT/'Pure_GGS_Amplifier_Per_Game.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();export=[{**m,'variant':'Pure_GGS','excluded':False} for m in baseline]+new+[{**x['original_record'],'rotation':x['original_record']['seat_rotation'],'excluded':True,'excluded_kind':x.get('excluded_kind','engine_timeout')} for x in failed_attempts]
 w.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in m.items()} for m in export)
print(json.dumps({'attempted':result['attempted'],'valid':result['valid'],'excluded':result['excluded'],'arms':[{'name':a['name'],'valid':a['valid'],'stability':a['stability'],'threat':a['contrasts']['threat']} for a in arms]},indent=2))

if (OUT/'Pure_GGS_Decision_Clock_Amendment.json').exists():
 result['decision_clock_amendment']=json.loads((OUT/'Pure_GGS_Decision_Clock_Amendment.json').read_text())
 (OUT/'Pure_GGS_Amplifier_Results.json').write_text(json.dumps(result,indent=2)+'\n')
