"""Advance only through a successful gate and saved recovery evidence."""
import fcntl,json,subprocess,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];OUT=WORK/'amplifier-slots'
with (OUT/'concurrency-gate/batch.lock').open() as lock:fcntl.flock(lock,fcntl.LOCK_SH)
p=json.loads((OUT/'concurrency-gate/performance.json').read_text());assert p['valid']==p['requested']==16
for script in ['check_concurrency_gate.py','adopt_concurrency_replays.py']:
 subprocess.run([sys.executable,str(HERE/script)],check=True,cwd=WORK)
archive=OUT/'Pure_GGS_Late_Timeout_Evidence.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=3) as t:
 for p in [OUT/'late-timeout-diagnostic',OUT/'late-timeout-unprofiled',OUT/'concurrency-gate-receipt.json',OUT/'Pure_GGS_Concurrency_Amendment.json']:
  t.add(p,arcname=str(p.relative_to(WORK)))
files=[OUT/'Pure_GGS_Concurrency_Amendment.json',archive]
request={'uploads':[{'local_path':str(p),'purpose':'create_library_file','directory_id':'6a8249fab85c8191a7fcb8390fc88fc5','library_artifact_type':'other'} for p in files]}
helper='/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.61/skills/library/scripts/library_upload.py'
r=subprocess.run([sys.executable,helper],input=json.dumps(request),text=True,capture_output=True,cwd=WORK);(OUT/'late-timeout-evidence-save.json').write_text(r.stdout);assert r.returncode==0
rs=json.loads(r.stdout)['results'];assert len(rs)==2 and all(x['status']=='succeeded' for x in rs)
print('Gate passed, original failed attempts retained, completed replays saved; resuming unchanged-deck experiment.',flush=True)
subprocess.run([sys.executable,str(HERE/'progress.py')],check=True,cwd=WORK)
