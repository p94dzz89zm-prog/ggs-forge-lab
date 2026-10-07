"""Verify finished-game audit streams; preserve evidence before removing duplicates."""
import argparse,gzip,hashlib,json,zlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--repair',action='store_true');p.add_argument('--prune-raw',action='store_true');a=p.parse_args();d=a.directory.resolve();rows=json.loads((d/'summary.json').read_text());saved=set(json.loads((d/'saved-game-keys.json').read_text())) if (d/'saved-game-keys.json').exists() else set();checks=[];freed=0
for r in rows:
 if r['status']!='completed':continue
 key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}"
 streams=sorted((d/'audit'/Path(r['log']).stem).glob('*.jsonl.gz'));assert len(streams)==8,(key,'missing all-seat audit streams',len(streams))
 for f in streams:
  raw=f.with_suffix('');repaired=False
  try:
   with gzip.open(f,'rb') as h:data=h.read()
  except (EOFError,OSError) as error:
   if not a.repair or not raw.exists():raise RuntimeError(f'Incomplete audit needs recovery: {f}') from error
   original=raw.read_bytes();partial=zlib.decompressobj(31).decompress(f.read_bytes());assert original.startswith(partial),f
   assert original.endswith(b'\n'),f
   for line in original.splitlines():json.loads(line)
   tmp=f.with_suffix('.gz.tmp')
   with gzip.open(tmp,'wb',compresslevel=5) as h:h.write(original)
   with gzip.open(tmp,'rb') as h:assert h.read()==original,f
   tmp.replace(f);data=original;repaired=True
  assert data.endswith(b'\n'),f
  for line in data.splitlines():json.loads(line)
  if raw.exists():
   original=raw.read_bytes();assert data.startswith(original),f
   if a.prune_raw:
    assert key in saved,'Only durable saved duplicates may be removed';freed+=len(original);raw.unlink()
  checks.append({'game':key,'path':str(f),'decoded_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'repaired_from_preserved_raw':repaired})
previous=json.loads((d/'audit-integrity.json').read_text()) if (d/'audit-integrity.json').exists() else {};historical={x['path']:x for x in previous.get('repaired',[])};historical.update({x['path']:x for x in checks if x['repaired_from_preserved_raw']})
receipt={'finished_games':len(rows),'audit_streams':len(checks),'repaired':list(historical.values()),'checks':checks,'redundant_raw_bytes_removed':freed}
(d/'audit-integrity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},indent=2))
