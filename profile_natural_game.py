"""Run one externally reserved, frozen natural-game performance diagnostic.

No allocation, game approval, strategy comparison or training is performed here.
The caller must persist its seed/conditions before invoking run. All output is
private and isolated. Engine result status, never process exit, defines outcome.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import subprocess
import time
from natural_game_inputs import fingerprint, verify_unchanged


def run(root):
    root=Path(root).resolve()
    if Path('/workspace') in root.parents:raise ValueError('Isolated output outside managed workspace required')
    manifest=json.loads((root/'inputs.json').read_text())
    verify_unchanged(manifest)
    result=root/'process.json'
    # Exclusive claim prevents repeating a failed or unknown attempt.
    with result.open('x') as f:
        json.dump(dict(status='running',seed=manifest['spec']['seed'],
                       started_utc=datetime.now(timezone.utc).isoformat(),input_sha256=manifest['input_sha256']),f)
        f.flush();os.fsync(f.fileno())
    before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
    with (root/'console.log').open('xb') as output:
        process=subprocess.Popen(manifest['spec']['command'],cwd=manifest['spec']['resource_root'],
                                 env=manifest['spec']['environment'],stdout=output,stderr=subprocess.STDOUT)
        timed_out=False
        try:code=process.wait(timeout=manifest['spec']['config']['outer_timeout_seconds'])
        except subprocess.TimeoutExpired:
            process.kill();code=process.wait();timed_out=True
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    outcome=dict(status='outer_timeout' if timed_out else 'process_exited',returncode=code,
        wall_seconds=time.monotonic()-start,user_cpu_seconds=after.ru_utime-before.ru_utime,
        system_cpu_seconds=after.ru_stime-before.ru_stime,max_rss_kib=after.ru_maxrss,
        seed=manifest['spec']['seed'],input_sha256=manifest['input_sha256'],
        rules_approved=False,training_admission=False)
    (root/'process-final.json').write_text(json.dumps(outcome,indent=2)+'\n')
    try:verify_unchanged(manifest)
    except Exception as error:
        (root/'input-drift.json').write_text(json.dumps(dict(error=str(error)))+'\n')
        raise
    (root/'inputs-post-run.json').write_text(json.dumps(dict(unchanged=True,input_sha256=manifest['input_sha256']))+'\n')
    # Preserve original running claim as an ownership/attempt record.
    print(json.dumps(outcome,sort_keys=True))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root');a=p.parse_args();run(a.root)
