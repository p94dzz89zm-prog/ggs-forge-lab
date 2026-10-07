"""Verify every audit record and gzip footer with bounded memory."""
import argparse,gzip,hashlib,json,shutil,zlib
from pathlib import Path
def validate(path,compressed=True):
 h=hashlib.sha256();n=0
 with (gzip.open(path,'rb') if compressed else path.open('rb')) as f:
  for line in f:
   assert line.endswith(b'\n'),path
   json.loads(line);h.update(line);n+=len(line)
 assert n>0,path
 return n,h.hexdigest()
def raw_prefix(raw,compressed,partial=False):
 with raw.open('rb') as original:
  if partial:
   decoder=zlib.decompressobj(31)
   with compressed.open('rb') as f:
    while chunk:=f.read(1<<20):
     pending=chunk
     while pending:
      output=decoder.decompress(pending,1<<20);pending=decoder.unconsumed_tail
      assert original.read(len(output))==output,compressed
  else:
   with gzip.open(compressed,'rb') as f:
    while chunk:=original.read(1<<20):assert f.read(len(chunk))==chunk,compressed
    while f.read(1<<20):pass
def main():
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--repair',action='store_true');p.add_argument('--prune-raw',action='store_true');a=p.parse_args();d=a.directory.resolve();rows=json.loads((d/'summary.json').read_text());saved=set(json.loads((d/'saved-game-keys.json').read_text())) if (d/'saved-game-keys.json').exists() else set();checks=[];freed=0
 for r in rows:
  if r['status']!='completed':continue
  key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";streams=sorted((d/'audit'/Path(r['log']).stem).glob('*.jsonl.gz'));assert len(streams)==8,(key,'missing all-seat audit streams',len(streams))
  for f in streams:
   raw=f.with_suffix('');repaired=False
   try:n,digest=validate(f)
   except (EOFError,OSError) as error:
    if not a.repair or not raw.exists():raise RuntimeError(f'Incomplete audit needs recovery: {f}') from error
    raw_prefix(raw,f,partial=True);expected=validate(raw,False);tmp=f.with_suffix('.gz.tmp')
    with raw.open('rb') as src,gzip.open(tmp,'wb',compresslevel=5) as out:shutil.copyfileobj(src,out)
    assert validate(tmp)==expected,f;tmp.replace(f);n,digest=expected;repaired=True
   if raw.exists():
    raw_prefix(raw,f)
    if a.prune_raw:
     assert key in saved,'Only durable saved duplicates may be removed';freed+=raw.stat().st_size;raw.unlink()
   checks.append({'game':key,'path':str(f),'decoded_bytes':n,'sha256':digest,'repaired_from_preserved_raw':repaired})
 previous=json.loads((d/'audit-integrity.json').read_text()) if (d/'audit-integrity.json').exists() else {};historical={x['path']:x for x in previous.get('repaired',[])};historical.update({x['path']:x for x in checks if x['repaired_from_preserved_raw']})
 receipt={'finished_games':len(rows),'audit_streams':len(checks),'repaired':list(historical.values()),'checks':checks,'redundant_raw_bytes_removed':freed,'verification':'every JSON record, gzip footer, decoded SHA256; memory bounded by one record'}
 (d/'audit-integrity.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['checks','repaired']},indent=2))
if __name__=='__main__':main()
