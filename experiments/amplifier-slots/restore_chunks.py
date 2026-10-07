"""Reconstruct completed checkpoints after authorized Library materialization."""
import argparse,gzip,hashlib,json,re,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];P=json.loads((HERE/'protocol.json').read_text());rows={};metadata={}
KNOWN_TRUNCATED={
 'Pure_GGS_Amplifier_stage-064_Part_14.tar.gz':'d15052a4e9446f30a006150593246001ce538bf5a1832cde3ec1ace59247266d',
 'Pure_GGS_Amplifier_stage-096_Part_46.tar.gz':'0c4fbe387878b5672c3ce5682387689caa3ed06af1c57fcc280de256d37a4f54',
 'Pure_GGS_Amplifier_stage-096_Part_69.tar.gz':'8ef2275786f10de888af7586c0d54284ec9370fbc84f84b553f58684ec3b0b5e',
 'Pure_GGS_Amplifier_stage-096_Part_72.tar.gz':'ac390e360c3781a85b1459e56942e7180b70b7ebf6bc9c3c6542bc5bc3ac18a6',
 'Pure_GGS_Amplifier_stage-096_Part_73.tar.gz':'b3a06124237dd6e6f3b3f5862c42bfd2a690eed1d929bca72dc2ff45bb9f157a',
}
parser=argparse.ArgumentParser();parser.add_argument('--skip-live-raw',action='store_true');parser.add_argument('folders',nargs='+');args=parser.parse_args();skipped=[]
for folder in args.folders:
 archives=sorted(Path(folder).rglob('Pure_GGS_Amplifier_*_Part_*.tar.gz'))
 for index,archive in enumerate(archives):
  if archive.name in KNOWN_TRUNCATED:
   # The retained original is known to be truncated. Every original identity
   # must be present unchanged, or explicitly superseded, in later complete
   # archives before this copy can be bypassed. No prefix is guessed.
   assert hashlib.sha256(archive.read_bytes()).hexdigest()==KNOWN_TRUNCATED[archive.name]
   sidecar=archive.with_name(archive.name.removesuffix('.tar.gz')+'.json');original=json.loads(sidecar.read_text());assert original['metadata']['protocol']==P
   coverage=[]
   for later in archives[index+1:]:
    side=later.with_name(later.name.removesuffix('.tar.gz')+'.json')
    if not side.exists():continue
    lm=json.loads(side.read_text())
    matched=[r for r in original['records'] if any(n==r or n.get('supersedes_failed_attempt')==r for n in lm['records'])]
    if not matched:continue
    assert lm['metadata']['protocol']==P
    with gzip.open(later,'rb') as verified:
     while verified.read(1<<20):pass
    with tarfile.open(later,'r|gz') as verified:
     for member in verified:
      if member.isfile():
       size=0
       with verified.extractfile(member) as payload:
        while chunk:=payload.read(1<<20):size+=len(chunk)
       assert size==member.size
    coverage.extend(matched)
   assert all(r in coverage for r in original['records']),'Incomplete archive has not been fully replaced; stop recovery'
   skipped.append({'archive':str(archive),'reason':'Every original identity covered unchanged or explicitly superseded by later verified full archives; original remains preserved in Library'});continue
  with tarfile.open(archive) as t:
   manifests=[m for m in t.getmembers() if m.name.startswith('Pure_GGS_Amplifier_') and m.name.endswith('.json') and '/' not in m.name];assert len(manifests)==1
   m=json.load(t.extractfile(manifests[0]));name=m['batch'];assert re.fullmatch(r'gate|deadline-gate|concurrency-gate|phase-reconciliation-gate|stage-\d{3}',name)
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
   members=[x for x in t.getmembers() if not(args.skip_live_raw and '/audit/' in x.name and x.name.endswith('.jsonl') and '/failed-attempts/' not in x.name)]
   t.extractall(WORK,members=members,filter='data')
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
if skipped:(WORK/'amplifier-slots/skipped-replaced-archives.json').write_text(json.dumps(skipped,indent=2)+'\n')
