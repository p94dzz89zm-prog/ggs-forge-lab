"""Verify two late-game replays without suppressing changed plays or board states."""
import difflib,gzip,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parents[2]/'amplifier-slots'
def records(p):
 with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:
  for line in f:yield json.loads(line)
def normalized(x):
 # Combat's attacker enumeration is unordered; blocker order and all other arrays remain intact.
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='combat' and isinstance(v,dict) and 'attackers' in v:v['attackers']=sorted(v['attackers'],key=lambda a:a['attacker_id'])
   normalized(v)
 elif isinstance(x,list):
  for v in x:normalized(v)
 return x
def canonical(p):
 lines=p.read_text().splitlines();out=[];i=0;phase=''
 while i<len(lines):
  l=lines[i];i+=1
  if l.startswith(('DragonMind Result:','Game Outcome: Match Duration')):continue
  if l.startswith('Phase: '):phase=l
  if l.startswith('Damage: ') and 'Damage Step' in phase:
   group=[l]
   while i<len(lines) and lines[i].startswith('Damage: '):group.append(lines[i]);i+=1
   out.append('SIMULTANEOUS DAMAGE:'+json.dumps(sorted(group)));continue
  if l.startswith('Combat: ') and (' to block ' in l or "didn't block" in l):
   group=[l.removeprefix('Combat: ')]
   while i<len(lines) and (' to block ' in lines[i] or "didn't block" in lines[i]):group.append(lines[i].removeprefix('Combat: '));i+=1
   out.append('BLOCK ASSIGNMENTS:'+json.dumps(sorted(group)));continue
  if l.startswith('Combat: ') and ' to attack ' in l and ' assigned ' in l:
   start,tail=l.split(' assigned ',1);attackers,end=tail.rsplit(' to attack ',1)
   names=re.findall(r'(.+? \(\d+\))(?:, | and |$)',attackers);assert len(names)==len(re.findall(r'\(\d+\)',attackers))
   out.append(start+' assigned '+json.dumps(sorted(s.strip(' ,') for s in names))+' to attack '+end);continue
  out.append(l)
 return out
def command(cmd):
 out=[];skip=False
 for v in cmd:
  if skip:skip=False;continue
  if v=='-c':out.extend([v,'DEADLINE']);skip=True
  elif v.startswith(('-Duser.home=','-Dforge.audit.directory=','-Ddragonmind.resultDirectory=')):out.append(v.split('=')[0]+'=OUTPUT')
  else:out.append(v)
 return out
def verify(original,replay,arms):
 old={r['variant']:r for r in json.loads((original/'summary.json').read_text()) if r['seed']==202610070 and r['seat_rotation']==2}
 new={r['variant']:r for r in json.loads((replay/'summary.json').read_text()) if r['seed']==202610070 and r['seat_rotation']==2};proof=[]
 for arm in arms:
  a,b=old[arm],new[arm];assert a['status']=='timeout' and b['status']=='completed' and a['seats']==b['seats'];assert command(a['command'])==command(b['command']);assert not any('StartFlightRecording' in v for v in b['command'])
  x,y=canonical(original/a['engine_transcript']),canonical(replay/b['engine_transcript']);assert len(y)>=len(x) and y[:len(x)]==x
  streams=[];label=Path(a['log']).stem
  for name in [f'{prefix}seat-{seat}.jsonl' for prefix in ['', 'evaluation-'] for seat in range(4)]:
   pa=original/'audit'/label/name;pb=replay/'audit'/label/name
   if not pa.exists():pa=pa.with_suffix('.jsonl.gz')
   if not pb.exists():pb=pb.with_suffix('.jsonl.gz')
   x=[normalized(r) for r in records(pa)];y=[normalized(r) for r in records(pb)]
   hashed=lambda rs:[hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest() for r in rs]
   additions=[];matched=0
   for op,i,j,k,l in difflib.SequenceMatcher(None,hashed(x),hashed(y),autojunk=False).get_opcodes():
    if op=='equal':matched+=j-i;continue
    assert op=='insert','Replay changes or deletes an original recorded state/decision'
    if i==len(x):continue # continuation beyond the timeout
    extra=y[k:l]
    if arm=='Pure_Slot_Karlach' and name=='seat-1.jsonl':
     assert len(extra)==1 and extra[0]['decision']['action']=='pass' and extra[0]['state']['turn']==60 and extra[0]['state']['phase']=='MAIN1'
    elif arm=='Pure_Slot_Karlach' and name=='evaluation-seat-2.jsonl':
     assert len(extra)==17 and all(r['kind']=='ai_evaluation' and r['turn']==61 and r['phase']=='MAIN1' and r['decision'] in ['CantPlayAi','CantPlaySa'] for r in extra)
    else:raise AssertionError('Unexpected additional audit event before original timeout')
    additions.append({'original_index':i,'replay_index':k,'records':extra})
   assert matched==len(x)
   streams.append({'stream':name,'original_records':len(x),'matched_original_records':matched,'replay_records':len(y),'extra_nonplay_hooks':additions})
  proof.append({'variant':arm,'seed':a['seed'],'rotation':a['seat_rotation'],'verified':True,'commands_equal_except_output_paths_and_deadline':True,'canonical_prefix_equal_after_representation_normalization':True,'canonical_original_lines':len(canonical(original/a['engine_transcript'])),'normalization':['Unordered combat attacker enumeration by card ID','Block assignments and simultaneous damage log rendering order; each full assignment/damage record retained'],'streams':streams,'engine_seconds':b['engine_ms']/1000,'original_deadline_seconds':600,'diagnostic_deadline_seconds':900,'diagnostic_workers':2})
 return proof
if __name__=='__main__':
 result=verify(OUT/'stage-064',OUT/'late-timeout-unprofiled',['Pure_Slot_Throne','Pure_Slot_Karlach'])
 (OUT/'late-timeout-unprofiled/verified-replay-proof.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: both original action/state prefixes retained; only enumerated nonplay hooks added.')
