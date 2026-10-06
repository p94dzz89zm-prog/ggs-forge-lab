import json,re
from pathlib import Path
out=[]
for directory in sorted(Path('pure-ggs').glob('batch-*')):
 for row in json.loads((directory/'summary.json').read_text()):
  if row['status']!='completed':continue
  idx=row['seats'].index('Pure_GGS');log=(directory/row['engine_transcript']).read_text()
  if 'Skullclamp targeting [Goro-Goro' not in log:continue
  checks=[];last_equipped=False
  for l in (directory/'audit'/Path(row['log']).stem/f'seat-{idx}.jsonl').open():
   x=json.loads(l);s=x.get('state');
   if not s:continue
   p=next((p for p in s['players'] if p['id']==idx),None)
   if not p:continue
   clamps={c['id'] for c in p['battlefield'] if c['name']=='Skullclamp'}
   equipped=[c for c in p['battlefield'] if c['name']=='Goro-Goro and Satoru' and clamps.intersection(c['attachments'])]
   if equipped and not last_equipped:checks.append({'global_turn':s['turn'],'survives':True,'power_toughness':[[c['power'],c['toughness']] for c in equipped]})
   last_equipped=bool(equipped)
  out.append({'seed':row['seed'],'rotation':row['seat_rotation'],'clamp_events':checks,'cleared':bool(checks) and all(c['survives'] and all(pt[1]>0 for pt in c['power_toughness']) for c in checks)})
Path('pure-ggs/clamp-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
