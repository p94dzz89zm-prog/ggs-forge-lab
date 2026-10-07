"""Reconstruct completed checkpoints after authorized Library materialization."""
import hashlib,json,re,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];P=json.loads((HERE/'protocol.json').read_text());rows={};metadata={}
for folder in sys.argv[1:]:
 for archive in sorted(Path(folder).rglob('Pure_GGS_Amplifier_*_Part_*.tar.gz')):
  with tarfile.open(archive) as t:
   manifests=[m for m in t.getmembers() if m.name.startswith('Pure_GGS_Amplifier_') and m.name.endswith('.json') and '/' not in m.name];assert len(manifests)==1
   m=json.load(t.extractfile(manifests[0]));name=m['batch'];assert re.fullmatch(r'gate|deadline-gate|concurrency-gate|stage-\d{3}',name)
   assert m['metadata']['protocol']==P
   if name in metadata:assert metadata[name]==m['metadata']
   metadata[name]=m['metadata'];rows.setdefault(name,{})
   for r in m['records']:
    key=(r['variant'],r['seed'],r['seat_rotation'])
    if key in rows[name] and rows[name][key]!=r:
     prior=rows[name][key]
     if r.get('supersedes_failed_attempt')==prior:pass
     elif prior.get('supersedes_failed_attempt')==r:continue
     else:raise AssertionError('Conflicting checkpoint record without explicit replay provenance')
    rows[name][key]=r
   t.extractall(WORK,filter='data')
for name,records in rows.items():
 # A later recovery archive contains completed gzip streams and the excluded
 # original in failed-attempts. Remove only bit-identical obsolete raw copies
 # left in the live directory by extraction of the earlier timeout archive.
 for r in records.values():
  if 'supersedes_failed_attempt' not in r:continue
  key=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";label=Path(r['log']).stem
  live=WORK/'amplifier-slots'/name/'audit'/label
  for raw in live.glob('*.jsonl'):
   historical=WORK/'amplifier-slots'/name/'failed-attempts'/key/'audit'/label/raw.name
   def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
     while chunk:=f.read(1<<20):h.update(chunk)
    return h.digest()
   if historical.exists() and sha(raw)==sha(historical):raw.unlink()
 d=WORK/'amplifier-slots'/name;d.mkdir(parents=True,exist_ok=True);ordered=list(records.values());(d/'metadata.json').write_text(json.dumps(metadata[name],indent=2)+'\n');(d/'summary.json').write_text(json.dumps(ordered,indent=2)+'\n');(d/'saved-game-keys.json').write_text(json.dumps([f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}" for r in ordered])+'\n')
 expected=metadata[name]['seeds']*4*len(metadata[name]['arms'])
 if len(records)==expected and all(r['status']=='completed' for r in ordered):(d/'performance.json').write_text(json.dumps({'attempted':len(records)+(len(json.loads((d/'failed-attempts.json').read_text())) if (d/'failed-attempts.json').exists() else 0),'valid':len(records),'requested':expected,'restored_from_saved_evidence':True})+'\n')
 print(name,'restored completed',len(records),'of',expected)
