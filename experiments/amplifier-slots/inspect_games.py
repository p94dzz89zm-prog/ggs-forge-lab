import gzip,json,re
from pathlib import Path
def inspect(directory,row,cards):
 directory=Path(directory);arm=row['variant'];idx=row['seats'].index(arm);name=f'Ai({idx+1})-{arm}';audit=directory/'audit'/Path(row['log']).stem/f'seat-{idx}.jsonl'
 if not audit.exists():audit=audit.with_suffix('.jsonl.gz')
 result={c:{'hand_seen':False,'battlefield_seen':False,'casts':0,'activated_or_triggered':0} for c in cards};clamp=[];prev=False
 with (gzip.open(audit,'rt') if audit.suffix=='.gz' else audit.open()) as f:
  for line in f:
   x=json.loads(line);s=x.get('state')
   if not s:continue
   player=next((p for p in s['players'] if p['id']==idx),None)
   if not player:continue
   for zone in ['hand','battlefield']:
    for card in player[zone]:
     if card['name'] in result:result[card['name']][zone+'_seen']=True
   clamps={c['id'] for c in player['battlefield'] if c['name']=='Skullclamp'}
   eq=[c for c in player['battlefield'] if c['name']=='Goro-Goro and Satoru' and clamps.intersection(c['attachments'])]
   if eq and not prev:clamp.append({'global_turn':s['turn'],'pt':[(c['power'],c['toughness']) for c in eq]})
   prev=bool(eq)
 text=(directory/row.get('engine_transcript',row['log'])).read_text()
 for kind,desc in re.findall(r'^Add To Stack: '+re.escape(name)+r' (cast|activated|triggered) (.+)$',text,re.M):
  for c,e in result.items():
   if kind=='cast' and desc==c:e['casts']+=1
   elif kind!='cast' and desc.startswith(c):e['activated_or_triggered']+=1
 flag='Skullclamp targeting [Goro-Goro and Satoru' in text
 return {'cards':result,'clamp_flag':flag,'clamp_observations':clamp,'clamp_cleared':not flag or bool(clamp) and all(t>0 for e in clamp for p,t in e['pt'])}
