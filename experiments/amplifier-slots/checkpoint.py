"""Persist only completed game records; excludes live jobs and source code."""
import json,subprocess,tarfile,fcntl,gzip,hashlib,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots'
HELPER='/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.61/skills/library/scripts/library_upload.py'
def verify_saved_bytes(results,expected):
 # A successful upload receipt alone did not detect four truncated hosted
 # copies. Verify newly saved bytes in a separate materialization directory.
 helper=Path(HELPER);sys.path.insert(0,str(helper.parent))
 from library_hosted_apps import HostedAppsClient
 checks=[]
 with tempfile.TemporaryDirectory(prefix='checkpoint-verify-',dir=OUT) as temporary:
  response=HostedAppsClient().call_tool('connector_openai_library','prepare_materialize',{'items':[{'library_file_id':r['library_file_id']} for r in results],'destination':{'directory':temporary}})
  while isinstance(response,dict) and 'structuredContent' in response:response=response['structuredContent']
  response=response.get('result',response);transfers=response['transfers'];assert len(transfers)==len(results)
  for result,transfer in zip(results,transfers):
   if transfer.get('library_file_id'):assert transfer['library_file_id']==result['library_file_id']
   path=Path(transfer.get('workspace_path') or Path(temporary)/result['file_name'])
   if transfer.get('workspace_path'):
    proc=subprocess.run([sys.executable,str(helper.parent/'library_file_transfer.py'),'apply-xattrs',str(path),result['library_file_id']],input=json.dumps(transfer.get('xattrs',[])),text=True,capture_output=True)
   else:
    proc=subprocess.run([sys.executable,str(helper.parent/'library_file_transfer.py'),'materialize',str(path)],input=json.dumps(transfer),text=True,capture_output=True)
   assert proc.returncode==0,'Saved-byte materialization failed'
   h=hashlib.sha256()
   with path.open('rb') as f:
    while chunk:=f.read(1<<20):h.update(chunk)
   check={'file_name':result['file_name'],'library_file_id':result['library_file_id'],'bytes':path.stat().st_size,'sha256':h.hexdigest()};check['passed']=check['sha256']==expected[result['file_name']]
   checks.append(check)
 return checks
def save(directory):
 directory=Path(directory).resolve()
 with (directory/'checkpoint.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);_save(directory)
def _save(directory):
 directory=Path(directory).resolve();receipts=OUT/'saved-chunks';receipts.mkdir(exist_ok=True);state=directory/'saved-game-keys.json'
 done=set(json.loads(state.read_text())) if state.exists() else set();rows=json.loads((directory/'summary.json').read_text());key=lambda r:f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";new=[r for r in rows if key(r) not in done]
 if not new:return
 index=max([int(p.stem.rsplit('-',1)[1]) for p in receipts.glob(directory.name+'-*.json')],default=0)+1;stem=f'Pure_GGS_Amplifier_{directory.name}_Part_{index:02d}';archive=OUT/(stem+'.tar.gz');manifest=OUT/(stem+'.json');receipt=receipts/f'{directory.name}-{index:02d}.json'
 manifest.write_text(json.dumps({'batch':directory.name,'metadata':json.loads((directory/'metadata.json').read_text()),'records':new,'cumulative_completed':len(rows),'only_finished_attempts':True},indent=2)+'\n')
 temporary_archive=archive.with_suffix('.gz.tmp')
 with tarfile.open(temporary_archive,'w:gz',compresslevel=3) as t:
  t.add(manifest,arcname=manifest.name)
  for p in [directory/'failed-attempts.json',directory/'run-amendments.json',directory/'adoption-receipt.json']:
   if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
  for p in [OUT/'execution-interruptions.json',OUT/'restoration-validation-receipt.json',OUT/'archive-copy-recovery.json',OUT/'Pure_GGS_Decision_Clock_Amendment.json',OUT/'decision-clock-gate-receipt.json']:
   if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
  if any('supersedes_failed_attempt' in r for r in new):
   proof_paths={OUT/r[field] for r in new for field in ['recovery_proof','recovery_gate','recovery_evidence'] if field in r}
   for p in [directory/'failed-attempts',*sorted(proof_paths)]:
    if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
  for r in new:
   label=Path(r['log']).stem
   for p in [directory/r['log'],directory/'engine-records'/label]:
    if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
   # Only canonical audit streams belong in a terminal checkpoint. Recursive
   # directory traversal can catch transient filesystem materialization files
   # that disappear before tar reads them, or redundant raw copies.
   audit=directory/'audit'/label
   for seat in range(4):
    for prefix in ['seat-','evaluation-seat-']:
     raw=audit/f'{prefix}{seat}.jsonl';compressed=raw.with_suffix('.jsonl.gz')
     p=compressed if compressed.exists() else raw
     if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
   for p in (directory/'analysis').glob(key(r)+'-*'):t.add(p,arcname=str(p.relative_to(WORK)))
 # Finalization success is not an archive-integrity check. Require the footer
 # and every member payload before marking any completion as durably saved.
 with gzip.open(temporary_archive,'rb') as verified:
  while verified.read(1<<20):pass
 members=0
 with tarfile.open(temporary_archive,'r|gz') as verified:
  for member in verified:
   if member.isfile():
    n=0
    with verified.extractfile(member) as payload:
     while chunk:=payload.read(1<<20):n+=len(chunk)
    assert n==member.size,(member.name,'incomplete archive payload')
   members+=1
 h=hashlib.sha256()
 with temporary_archive.open('rb') as verified:
  while chunk:=verified.read(1<<20):h.update(chunk)
 integrity={'gzip_footer_verified':True,'all_member_payloads_verified':True,'members':members,'bytes':temporary_archive.stat().st_size,'sha256':h.hexdigest()}
 temporary_archive.replace(archive)
 request={'uploads':[{'local_path':str(p.resolve()),'purpose':'create_library_file','directory_id':'6a8249fab85c8191a7fcb8390fc88fc5','library_artifact_type':'other'} for p in [manifest,archive]]}
 proc=subprocess.run(['python3',HELPER],input=json.dumps(request),text=True,capture_output=True,cwd=WORK);receipt.write_text(proc.stdout)
 if proc.returncode:raise RuntimeError('Checkpoint save failed; inspect private receipt before advancing')
 results=json.loads(proc.stdout)['results'];assert len(results)==2 and all(x['status']=='succeeded' for x in results)
 receipt_data=json.loads(proc.stdout);receipt_data['archive_integrity']=integrity
 expected={manifest.name:hashlib.sha256(manifest.read_bytes()).hexdigest(),archive.name:integrity['sha256']}
 checks=verify_saved_bytes(results,expected);receipt_data['post_upload_integrity']=checks;receipt.write_text(json.dumps(receipt_data,indent=2)+'\n')
 assert all(c['passed'] for c in checks),'Saved bytes differ from verified originals; stop before advancing saved status'
 done.update(key(r) for r in new);tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(sorted(done))+'\n');tmp.replace(state)
 print(json.dumps({'saved_batch':directory.name,'new_saved_games':len(new),'cumulative_saved':len(done),'files':[x['file_name'] for x in results]}),flush=True)
if __name__=='__main__':
 import sys;save(Path(sys.argv[1]))
