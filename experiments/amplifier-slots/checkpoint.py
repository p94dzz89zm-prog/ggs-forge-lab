"""Persist only completed game records; excludes live jobs and source code."""
import json,subprocess,tarfile,fcntl
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots'
HELPER='/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.61/skills/library/scripts/library_upload.py'
def save(directory):
 directory=Path(directory).resolve()
 with (directory/'checkpoint.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);_save(directory)
def _save(directory):
 directory=Path(directory).resolve();receipts=OUT/'saved-chunks';receipts.mkdir(exist_ok=True);state=directory/'saved-game-keys.json'
 done=set(json.loads(state.read_text())) if state.exists() else set();rows=json.loads((directory/'summary.json').read_text());key=lambda r:f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}";new=[r for r in rows if key(r) not in done]
 if not new:return
 index=len(list(receipts.glob(directory.name+'-*.json')))+1;stem=f'Pure_GGS_Amplifier_{directory.name}_Part_{index:02d}';archive=OUT/(stem+'.tar.gz');manifest=OUT/(stem+'.json');receipt=receipts/f'{directory.name}-{index:02d}.json'
 manifest.write_text(json.dumps({'batch':directory.name,'metadata':json.loads((directory/'metadata.json').read_text()),'records':new,'cumulative_completed':len(rows),'only_finished_attempts':True},indent=2)+'\n')
 with tarfile.open(archive,'w:gz',compresslevel=3) as t:
  t.add(manifest,arcname=manifest.name)
  for p in [directory/'failed-attempts.json',directory/'run-amendments.json',directory/'adoption-receipt.json']:
   if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
  if any('supersedes_failed_attempt' in r for r in new):
   for p in [directory/'failed-attempts',OUT/'deadline-gate-receipt.json',OUT/'timeout-replay-unprofiled/replay-check.json']:
    if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
  for r in new:
   label=Path(r['log']).stem
   for p in [directory/r['log'],directory/'audit'/label,directory/'engine-records'/label]:
    if p.exists():t.add(p,arcname=str(p.relative_to(WORK)))
   for p in (directory/'analysis').glob(key(r)+'-*'):t.add(p,arcname=str(p.relative_to(WORK)))
 request={'uploads':[{'local_path':str(p.resolve()),'purpose':'create_library_file','directory_id':'6a8249fab85c8191a7fcb8390fc88fc5','library_artifact_type':'other'} for p in [manifest,archive]]}
 proc=subprocess.run(['python3',HELPER],input=json.dumps(request),text=True,capture_output=True,cwd=WORK);receipt.write_text(proc.stdout)
 if proc.returncode:raise RuntimeError('Checkpoint save failed; inspect private receipt before advancing')
 results=json.loads(proc.stdout)['results'];assert len(results)==2 and all(x['status']=='succeeded' for x in results)
 done.update(key(r) for r in new);tmp=state.with_suffix('.tmp');tmp.write_text(json.dumps(sorted(done))+'\n');tmp.replace(state)
 print(json.dumps({'saved_batch':directory.name,'new_saved_games':len(new),'cumulative_saved':len(done),'files':[x['file_name'] for x in results]}),flush=True)
if __name__=='__main__':
 import sys;save(Path(sys.argv[1]))
