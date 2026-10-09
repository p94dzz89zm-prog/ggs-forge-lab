"""Audit actual-game gate; no deck-performance claims from gate cases."""
import gzip,hashlib,importlib.util,json,sys
from pathlib import Path
from measure import extract
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('inspect_cards',ROOT/'experiments/amplifier-slots/inspect_games.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
out=Path(sys.argv[1]);rows=json.loads((out/'summary.json').read_text());assert len(rows)==16 and all(r['status']=='completed' for r in rows)
checks=[];all_cards=set()
for r in rows:
 k=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";m=json.loads((out/'analysis'/(k+'-metrics.json')).read_text());t=json.load(gzip.open(out/'analysis'/(k+'-timeline.json.gz'),'rt'))
 assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
 ext=extract(out,r,m,t);(out/'analysis'/(k+'-extended.json')).write_text(json.dumps(ext,indent=2)+'\n');all_cards.update(c for c,e in ext['cards'].items() if e['battlefield_seen'])
 clamp=audit.inspect(out,r,[]);assert clamp['clamp_cleared'],'Commander clamp requires review'
 streams=[]
 for p in sorted((out/'audit'/Path(r['log']).stem).glob('*.jsonl.gz')):
  count=0;h=hashlib.sha256()
  with gzip.open(p,'rb') as f:
   for line in f:json.loads(line);h.update(line);count+=1
  streams.append({'name':p.name,'rows':count,'decoded_sha256':h.hexdigest()})
 assert len(streams)==8 and all(s['rows']>0 for s in streams)
 checks.append({'variant':r['variant'],'seed':r['seed'],'rotation':r['seat_rotation'],'creations_reconciled':True,'life_match':1,'clamp':clamp,'streams':streams,'student_copies':ext['student_copies']})
receipt={'passed':True,'games':16,'excluded_from_experimental_estimates':True,'checks':checks,'cards_observed_battlefield':sorted(all_cards),'rules_fidelity':'Actual Forge rules and unchanged pilot; imported scripts, logged states and completed games reviewed. The gate cannot exhaust every possible card interaction.'}
(out.parent/'gate-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS:16 games,128 valid audit streams, creations/life states reconciled')
