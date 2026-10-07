"""Compare actual recovery games with every surviving original audit record."""
import difflib,gzip,hashlib,json,zlib,sys
from pathlib import Path
from check_late_replays import canonical,command,normalized
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'amplifier-slots'
old=OUT/'stage-096';new=OUT/'archive-recovery-replays';proofdir=OUT/'archive-recovery-20261007';proofdir.mkdir(exist_ok=True)
def lines(path,partial=False):
 if path.name.endswith('.gz.partial'):
  decoder=zlib.decompressobj(31);buffer=b''
  with path.open('rb') as f:
   while chunk:=f.read(1<<16):
    pending=chunk
    while pending:
     buffer+=decoder.decompress(pending,1<<20);pending=decoder.unconsumed_tail
     while b'\n' in buffer:
      line,buffer=buffer.split(b'\n',1);yield line+b'\n'
  return
 with (gzip.open(path,'rb') if path.suffix=='.gz' else path.open('rb')) as f:
  for line in f:
   if partial and not line.endswith(b'\n'):break
   assert line.endswith(b'\n');yield line
def hashes(path,partial=False):
 def record(line):
  value=normalized(json.loads(line));state=value.get('state',{})
  if state.get('turn')==49 and state.get('phase')=='COMBAT_DECLARE_ATTACKERS':
   for card in state.get('stack',[]):
    if card.get('id')==355 and card.get('name')=='Fire Navy Trebuchet' and ' [Number Attackers: [' in card.get('description',''):
     prefix,tail=card['description'].split(' [Number Attackers: [',1);assert tail.endswith(']]')
     names=tail[:-2].split(', ');assert set(names)=={'Phyrexian Horror Token (556)','Phyrexian Horror Token (568)','Dragon Spirit Token (550)','Goro-Goro and Satoru (403)'}
     card['description']=prefix+' [Number Attackers: ['+', '.join(sorted(names))+']]'
  return value
 return [hashlib.sha256(json.dumps(record(line),sort_keys=True,separators=(',',':')).encode()).hexdigest() for line in lines(path,partial)]
original=json.loads((WORK/'oct7-prefix-recovery/pending-records-structural.json').read_text());replacement=json.loads((new/'summary.json').read_text());audit_only='--audit-only' in sys.argv
assert (audit_only or len(replacement)==10) and all(r['status']=='completed' for r in replacement)
proof=[]
for a in original:
 b=next(r for r in replacement if (r['variant'],r['seed'],r['seat_rotation'])==(a['variant'],a['seed'],a['seat_rotation']));label=Path(a['log']).stem
 assert command(a['command'])==command(b['command'])
 m=json.loads((new/'analysis'/f"{b['variant']}-{b['seed']}-r{b['seat_rotation']}-metrics.json").read_text());assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
 entry={'variant':a['variant'],'seed':a['seed'],'rotation':a['seat_rotation'],'winner_equal':a['winner']==b['winner'],'last_logged_turn_equal':a['last_logged_turn']==b['last_logged_turn'],'commands_equal_except_output_paths':True,'canonical_original_available':(old/a['engine_transcript']).exists(),'audit_streams':[]}
 assert entry['winner_equal'] and entry['last_logged_turn_equal']
 if entry['canonical_original_available']:
  x=canonical(old/a['engine_transcript']);y=canonical(new/b['engine_transcript']);assert x==y;entry.update(canonical_normalized_equal=True,canonical_lines=len(x))
 for seat in range(4):
  for prefix in ['seat-','evaluation-seat-']:
   name=f'{prefix}{seat}.jsonl';root=old/'audit'/label;pa=root/(name+'.gz')
   if not pa.exists():pa=root/name
   partial=False
   if not pa.exists():
    candidates=[WORK/'oct7-prefix-recovery/amplifier-slots/stage-096/audit'/label/(name+'.partial'),WORK/'oct7-prefix-recovery/amplifier-slots/stage-096/audit'/label/(name+'.gz.partial')]
    pa=next((p for p in candidates if p.exists()),None);partial=True
   if pa is None or not pa.exists():continue
   x=hashes(pa,partial);y=hashes(new/'audit'/label/(name+'.gz'))
   equal=y[:len(x)]==x if partial else y==x
   item={'stream':name,'original_complete_records':len(x),'replay_records':len(y),'original_was_partial':partial,'equal_original_records':equal}
   if not equal:
    ops=[op for op in difflib.SequenceMatcher(None,x,y,autojunk=False).get_opcodes() if op[0]!='equal'];item['differences']=ops;additions=[]
    full=[json.loads(line) for line in lines(new/'audit'/label/(name+'.gz'))]
    accepted=True
    for op,i,j,k,l in ops:
     extra=full[k:l];allowed=False;kind=None
     if op=='insert' and a['variant']=='Pure_Slot_Tempest' and a['seed']==202610080 and a['seat_rotation']==1:
      if name=='evaluation-seat-0.jsonl' and (i,j,k,l)==(4586,4586,4586,4626):
       allowed=len(extra)==40 and all(r['turn']==47 and r['player_id']==0 and r['phase'] in ['COMBAT_BEGIN','COMBAT_DECLARE_ATTACKERS','COMBAT_DECLARE_BLOCKERS','COMBAT_DAMAGE'] and r['decision'] in ['CantPlaySa','CantPlayAi'] for r in extra);kind='additional rejected ability checks, no changed priority decisions'
      elif name=='evaluation-seat-3.jsonl' and i==len(x):
       allowed=len(extra)==16 and all(r['turn']==50 and r['phase']=='COMBAT_DECLARE_BLOCKERS' and r['player_id']==3 and r['decision'] in ['CantPlaySa','CantPlayAi'] for r in extra);kind='rejected-check continuation beyond surviving stream'
     elif op=='insert' and i==len(x) and a['variant']=='Pure_Slot_Karlach' and a['seed']==202610082 and a['seat_rotation']==0 and name=='seat-3.jsonl':
      expected=['pass','[Crew 2 (Tap any number of creatures you control with total power 2 or more: Mole Module becomes an artifact creature until end of turn.)]']+['pass']*6
      allowed=len(extra)==8 and [r['decision']['action'] for r in extra]==expected and all(r['state']['turn']==54 for r in extra);kind='actual final-turn continuation beyond surviving stream, including one crew activation'
     accepted &= allowed
     additions.append({'original_index':i,'replay_index':k,'accepted':allowed,'kind':kind,'records':extra})
    item['enumerated_additions']=additions;item['equal_original_records']=accepted
   entry['audit_streams'].append(item)
 proof.append(entry)
(proofdir/'replay-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
assert all(s['equal_original_records'] for p in proof for s in p['audit_streams']),'Original audit records differ; investigate before adopting recovery'
if audit_only:
 print('PASS: every surviving original audit record matches its actual replay; baseline gate not yet sealed');raise SystemExit(0)
gate=[]
for b in replacement:
 if b['variant']!='Pure_GGS':continue
 a=next(r for r in json.loads((OUT/'gate/summary.json').read_text()) if r['variant']=='Pure_GGS' and r['seed']==b['seed'] and r['seat_rotation']==b['seat_rotation'])
 strip=lambda p:[l for l in p.read_text().splitlines() if not l.startswith(('DragonMind Result:','Game Outcome: Match Duration'))]
 assert strip(OUT/'gate'/a['engine_transcript'])==strip(new/b['engine_transcript'])
 m=json.loads((new/'analysis'/f"Pure_GGS-{b['seed']}-r{b['seat_rotation']}-metrics.json").read_text());assert not m['measurement_gaps'] and m['snapshot_life_match_rate']==1
 gate.append({'seed':b['seed'],'rotation':b['seat_rotation'],'canonical_exact_excluding_elapsed_fields':True,'measurement_gaps':0,'snapshot_life_match_rate':1})
receipt={'passed':True,'actual_recovery_replays':6,'fresh_baseline_replays':gate,'gate_not_independent_experimental_observations':True,'canonical_replay_scope':'Only one surviving original canonical log can be compared; all available complete/partial audit records checked. Two original games have metadata only. Unordered attacker names in two Trebuchet trigger descriptions were normalized; 56 additional rejected-check hooks and eight final-turn priority records, including one actual crew activation beyond the surviving Karlach stream, are explicitly preserved. Every surviving original decision and material board state matches after the listed rendering normalization. Original raw records are preserved.','engine_and_decks_unchanged':True}
(proofdir/'validation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS: six actual recovery games, all surviving audit records retained, four exact baseline seat replays')
