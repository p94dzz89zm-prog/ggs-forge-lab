"""Run evidence producers outside the synchronized workspace; transport sealed bytes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import milestone_checkpoint as checkpoint


def outside_workspace(base, archive):
    base=Path(base).resolve();archive=Path(archive).resolve()
    if base==Path('/workspace') or Path('/workspace') in base.parents or base==archive.parent:
        raise ValueError('Active evidence root must be outside the synchronized workspace')
    base.mkdir(parents=True,exist_ok=True)
    return base


def run(command, archive, source_commit, scratch_base='/tmp', timeout=300):
    """Run one allocated stage. Failed raw output is retained, never auto-retried.

    The command receives {output} as a fresh isolated directory. Only a sealed
    archive crosses back. Completion means stage completion, NOT rules approval.
    Actual game commands must retain the existing writer and learning gates.
    """
    archive=Path(archive).resolve()
    if archive.exists():raise FileExistsError(archive)
    base=outside_workspace(scratch_base,archive)
    root=Path(tempfile.mkdtemp(prefix='dragonmind-evidence-',dir=base))
    output=root/'output';output.mkdir()
    argv=[part.replace('{output}',str(output)) for part in command]
    if not command or not any('{output}' in p for p in command):raise ValueError('Explicit {output} command argument required')
    timed_out=False
    try:
        proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
        rc=proc.returncode;console=proc.stdout
    except subprocess.TimeoutExpired as error:
        rc=None;timed_out=True;console=error.stdout or b''
    (root/'producer.log').write_bytes(console)
    status={'format':1,'returncode':rc,'timeout':timed_out,'stage_complete':rc==0 and not timed_out,
            'rules_approval':False,'learning_admission':False,'command':command,
            'active_root_outside_workspace':True}
    (root/'producer-status.json').write_text(json.dumps(status,indent=2)+'\n')
    files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and 'runtime-home' not in p.parts)
    sealed=root.parent/(root.name+'.zip')
    receipt=checkpoint.create(root,sealed,{'milestone':'isolated-evidence-stage','source_commit':source_commit,'rules_approval':False,'producer_complete':status['stage_complete']},files)
    checkpoint.verify(sealed,receipt['sha256'])
    archive.parent.mkdir(parents=True,exist_ok=True)
    # Publish the already sealed inode atomically and exclusively. If the
    # isolated root and destination are on different filesystems, fail closed
    # and retain the sealed source rather than expose a partial archive.
    os.link(sealed,archive)
    d=os.open(archive.parent,os.O_DIRECTORY)
    try:os.fsync(d)
    finally:os.close(d)
    checkpoint.verify(archive,receipt['sha256'])
    return {'archive':str(archive),'sha256':receipt['sha256'],'producer':status,
            'isolated_root':str(root),'retention':'Original isolated root retained; no live workspace tree is resumed'}


def restore(archive, sha256, scratch_base='/tmp'):
    """Verify then restore into a fresh external tree, never merge live evidence."""
    base=outside_workspace(scratch_base,archive)
    parent=Path(tempfile.mkdtemp(prefix='dragonmind-restore-',dir=base))
    target=parent/'evidence'
    checkpoint.restore(archive,sha256,target)
    return target


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--source-commit',required=True)
    p.add_argument('--scratch-base',default='/tmp');p.add_argument('--timeout',type=int,default=300)
    p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args()
    cmd=a.command[1:] if a.command[:1]==['--'] else a.command
    result=run(cmd,a.archive,a.source_commit,a.scratch_base,a.timeout)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['producer']['stage_complete'] else 1)
