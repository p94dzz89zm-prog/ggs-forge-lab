"""Remove only durable local duplicates; keep canonical logs and analysis available."""
import fcntl,hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'amplifier-slots';removed=[]
# Receipt order is preserved; upload success alone never substitutes for analysis verification.
for f in sorted((OUT/'saved-chunks').glob('*.json')):
 receipt=json.loads(f.read_text());results=receipt.get('results',[])
 if len(results)!=2 or not all(x['status']=='succeeded' for x in results):continue
 for r in results:
  name=r['file_name']
  if not name.endswith('.tar.gz'):continue
  p=OUT/name
  if p.exists():
   removed.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'save_receipt':str(f),'library_file_id':r.get('library_file_id')});p.unlink()
for d in sorted(OUT.glob('stage-*')):
 if not (d/'performance.json').exists() or not (d/'audit').exists():continue
 perf=json.loads((d/'performance.json').read_text())
 if perf['valid']!=perf['requested']:continue
 lock=(d/'batch.lock').open('a')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:continue
 rows=json.loads((d/'summary.json').read_text());keys={f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}" for r in rows};saved=set(json.loads((d/'saved-game-keys.json').read_text()))
 integrity=json.loads((d/'audit-integrity.json').read_text()) if (d/'audit-integrity.json').exists() else {}
 if not (keys.issubset(saved) and integrity.get('finished_games')==len(rows) and integrity.get('audit_streams')==8*len(rows)):continue
 if not all((d/'analysis'/(k+'-inspection.json')).exists() for k in keys):continue
 size=sum(p.stat().st_size for p in (d/'audit').rglob('*') if p.is_file());removed.append({'path':str(d/'audit'),'bytes':size,'verified_integrity_receipt':str(d/'audit-integrity.json'),'durable_games':len(keys),'reason':'All eight audit streams per game checked; every game saved; analysis/exposure cache and canonical logs retained.'});shutil.rmtree(d/'audit');lock.close()
receipt=OUT/'local-duplicate-cleanup.json';history=json.loads(receipt.read_text()) if receipt.exists() else [];history.extend(removed);receipt.write_text(json.dumps(history,indent=2)+'\n');print(json.dumps({'removed_duplicates':len(removed),'bytes_freed':sum(x['bytes'] for x in removed)}))
