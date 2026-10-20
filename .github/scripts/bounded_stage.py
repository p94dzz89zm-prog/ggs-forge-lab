#!/usr/bin/env python3
"""Run a bounded CI stage, persist status before execution and log while running."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def atomic(path, value):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2); f.flush(); os.fsync(f.fileno())
    os.replace(temp, path)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage', required=True)
    p.add_argument('--seconds', type=int, required=True)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a=p.parse_args()
    if not a.stage.replace('-','').isalnum() or not 1 <= a.seconds <= 420 or not a.command:
        p.error('Safe stage name, command, and budget 1..420 required')
    out=Path('ci-results');out.mkdir(exist_ok=True)
    status=out/(a.stage+'.json');log=out/(a.stage+'.log')
    if status.exists() or log.exists():
        raise SystemExit('Existing attempt retained; no implicit retry')
    command=a.command[1:] if a.command[0]=='--' else a.command
    row={'stage':a.stage,'status':'running','command':command,'budget_seconds':a.seconds,
         'source_commit':os.environ.get('GITHUB_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
         'run_id':os.environ.get('GITHUB_RUN_ID'), 'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
         'started_utc':datetime.now(timezone.utc).isoformat(), 'trusted_training_updates':0}
    atomic(status,row);start=time.monotonic()
    with log.open('xb') as f:
        try:
            proc=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                code=proc.wait(timeout=a.seconds)
                row.update(status='passed' if code==0 else 'failed',returncode=code)
            except subprocess.TimeoutExpired:
                import signal
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                row.update(status='timeout',returncode=None)
        except OSError as error:
            row.update(status='launch_failed',error=str(error),returncode=None)
        f.flush();os.fsync(f.fileno())
    row.update(elapsed_seconds=round(time.monotonic()-start,3),log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    atomic(status,row)
    sys.stdout.write(log.read_text(errors='replace'));print(json.dumps(row))
    return 0 if row['status']=='passed' else 1
if __name__=='__main__': raise SystemExit(main())
