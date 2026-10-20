"""Verify writer-origin completion, counts and hashes; never repair evidence."""
import hashlib,json
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
def stream_summary(path):
 h=hashlib.sha256();size=records=0;tail=b''
 with path.open('rb') as stream:
  while chunk:=stream.read(1024*1024):
   h.update(chunk);size+=len(chunk);records+=chunk.count(b'\n');tail=chunk[-1:]
 return h.hexdigest(),size,records,tail
def verify(root,record_dir,seed,require_ownership=True):
 root=Path(root).resolve(); directory=Path(record_dir)
 m=json.loads((directory/f'{seed}.evidence.json').read_text())
 if m.get('format')!=1 or m.get('seed')!=seed or m.get('write_status')!='complete' or m.get('completion_marker')!='DRAGONMIND_EVIDENCE_COMPLETE':raise ValueError('Missing writer completion')
 transcript=(directory/f'{seed}.log').read_bytes();result=(directory/f'{seed}.json').read_bytes()
 if sha(transcript)!=m['transcript_sha256'] or len(transcript.splitlines())!=m['transcript_records'] or sha(result)!=m['result_sha256']:raise ValueError('Canonical evidence changed')
 if json.loads(result).get('status') not in ('completed','completed_draw'):raise ValueError('Incomplete game result')
 if sum(l.startswith(b'DragonMind Result: ') for l in transcript.splitlines())!=1:raise ValueError('Missing or duplicate result marker')
 listed=set();snapshots=0;seat_files=set();owners={};referee_report=None
 for receipt in m['streams']:
  name=receipt['file'];relative=Path(name);p=root/relative
  if relative.is_absolute() or '..' in relative.parts or p.is_symlink() or not p.resolve().is_relative_to(root) or name in listed:raise ValueError('Unsafe or duplicate evidence path')
  listed.add(name);digest,size,records,tail=stream_summary(p)
  if receipt.get('game_id')!=m['game_id'] or receipt.get('write_status')!='complete' or digest!=receipt['sha256'] or size!=receipt['bytes']:raise ValueError('Stream hash/size/status mismatch')
  if json.loads(p.with_name(p.name+'.receipt.json').read_text())!=receipt:raise ValueError('Stream receipt mismatch')
  if p.name=='referee-events.jsonl':
   from referee_tape import inspect
   referee_report=inspect(p)
  if records!=receipt['records'] or tail!=b'\n':raise ValueError('Stream record count/tail mismatch')
  with p.open('rb') as stream:
   for number,line in enumerate(stream,1):
    row=json.loads(line)
    if row.get('evidence_game_id')!=m['game_id'] or row.get('stream_sequence')!=number:raise ValueError('Stream sequence/game mismatch')
    state=row.get('state')
    if state:
     snapshots+=1;seat_files.add(p.name)
     active_ids={player['id'] for player in state['players']}
     for player in state['players']:
      if player['id']!=state['viewer_id'] and 'hand' in player:raise ValueError('Opponent hand leaked')
      if 'library' in player or 'library_order' in player:raise ValueError('Library leaked')
      for zone in ('battlefield','graveyard','command','exile','hand'):
       for card in player.get(zone,[]):
        if require_ownership and (type(card.get('owner_id')) is not int or type(card.get('controller_id')) is not int or not card.get('zone')):raise ValueError('Missing ownership/control/zone evidence')
        if require_ownership:
         if card['owner_id'] not in active_ids:raise ValueError('Departed owner object remains')
         if 'id' in card:
          if card['id'] in owners and owners[card['id']]!=card['owner_id']:raise ValueError('Card owner changed across snapshots')
          owners[card['id']]=card['owner_id']
  
 actual={str(p.relative_to(root)) for p in (root/'audit').rglob('*.jsonl')}
 if actual!=listed:raise ValueError('Unbound or missing audit stream')
 if len(seat_files)!=4:raise ValueError('Missing four-seat snapshot coverage')
 if list((root/'audit').rglob('*.partial')):raise ValueError('Unfinalized audit stream')
 return {'passed':True,'game_id':m['game_id'],'streams':len(listed),'snapshots':snapshots,'ownership_fields_verified':require_ownership,'referee_tape':referee_report,'rules_validated':False,'learning_admission':False}
