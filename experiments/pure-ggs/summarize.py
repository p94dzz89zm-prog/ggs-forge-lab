import json,statistics,collections,math,sys,random
from pathlib import Path

def summarize(rows):
 valid=[r for r in rows if r['status']=='completed' and not r.get('excluded')];ig=[r for r in valid if r.get('first_dragon_turn') is not None]
 def rate(pred,pop):
  n=len(pop);k=sum(bool(pred(r)) for r in pop)
  if not n:return {'n':0,'successes':0,'percent':None}
  z=1.96;den=1+z*z/n;centre=(k/n+z*z/(2*n))/den;half=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/den
  return {'n':n,'successes':k,'percent':round(k/n*100,2),'wilson_95':[round(100*(centre-half),2),round(100*(centre+half),2)]}
 def timing(key):
  x=[r[key] for r in valid if r.get(key) is not None];return {'observed':len(x),'mean':round(statistics.mean(x),3) if x else None,'median':statistics.median(x) if x else None}
 out={'attempts':len(rows),'valid':len(valid),'excluded':len(rows)-len(valid),'ignited':len(ig),'win_rate':rate(lambda r:r['win'],valid),'timing':{k:timing(k) for k in ['ggs_cast_turn','first_dragon_turn','second_dragon_turn','threat_turn']},'rates':{k:rate(lambda r,k=k:r.get(k),ig) for k in ['within_one','within_two','basic_turn','strong_turn','threat_turn']},'stall_categories':dict(collections.Counter(r.get('primary_stall_category') for r in valid)), 'post_ignition_stall_categories':dict(collections.Counter(r.get('primary_stall_category') for r in ig)), 'measurement_gaps':[(r['seed'],r['rotation'],r['measurement_gaps']) for r in valid if r.get('measurement_gaps')]}
 out['dependency']={label:{c:rate(lambda r,label=label,c=c:(r.get(label+'_dependency') or {}).get('class')==c,ig) for c in ['NATURAL GGS','AMPLIFIED GGS','AMPLIFIER-DEPENDENT']} for label in ['basic','strong','threat']}
 threats=[r for r in ig if r.get('threat_turn') is not None]
 out['threats_without_material_amp']=rate(lambda r:(r.get('threat_dependency') or {}).get('class')=='NATURAL GGS',threats)
 out['threats_without_any_prior_amp']=rate(lambda r:not r.get('threat_amplifier_present_before'),threats)
 out['dependency_uncertain']={label:sum(bool((r.get(label+'_dependency') or {}).get('dependency_uncertain')) for r in ig) for label in ['basic','strong','threat']}
 wipes=[w for r in valid for w in r.get('wipe_events',[])];out['recovery']=rate(lambda w:w.get('recovered'),wipes)
 # Seed-cluster bootstrap preserves the four seat-rotated games sharing each seed.
 groups=collections.defaultdict(list)
 for r in valid:groups[r['seed']].append(r)
 rng=random.Random(20261006);keys=sorted(groups);bs=collections.defaultdict(list)
 for _ in range(2000):
  sample=[r for key in rng.choices(keys,k=len(keys)) for r in groups[key]] if keys else [];ignited=[r for r in sample if r.get('first_dragon_turn') is not None]
  if not ignited:continue
  for k in out['rates']:bs[k].append(100*sum(bool(r.get(k)) for r in ignited)/len(ignited))
 out['seed_cluster_bootstrap_95']={k:[round(sorted(v)[int(len(v)*q)],2) for q in (.025,.975)] for k,v in bs.items()}
 out['interval_note']='Wilson treats games independently; seed-cluster bootstrap resamples whole four-seat seed blocks. Neither captures AI-model uncertainty.'
 return out
if __name__=='__main__':
 rows=[]
 for p in sys.argv[1:]:rows+=json.loads(Path(p).read_text())
 print(json.dumps(summarize(rows),indent=2))
