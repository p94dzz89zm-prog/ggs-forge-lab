#!/usr/bin/env python3
"""Save a consistent, immutable learner DB and audit actual learning readiness.

Uses SQLite backup, including committed WAL data. Never treats a raw reward,
checkpoint save, or scoped regression as full-game learning admission.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from adaptive_pilot import PROFILES
from learning_gate import FULL_SCOPE


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=5)


def inspect_model(path, check_evidence=True):
    from review_experience import profile_learning_gate
    db = readonly(path)
    db.row_factory = sqlite3.Row
    try:
        if db.execute('PRAGMA integrity_check').fetchall()[0][0] != 'ok':
            raise ValueError('SQLite integrity failure')
        expected = {'episodes', 'reviews', 'review_events'}
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not expected <= tables:
            raise ValueError('Missing learner schema')
        rows = list(db.execute('SELECT * FROM episodes ORDER BY run,idx'))
        accepted = {(r['run'], r['idx']) for r in db.execute(
            "SELECT * FROM reviews WHERE status='pass' AND scope=?", (FULL_SCOPE,))}
        statuses = {}
        admitted, issues, by_context = 0, [], {}
        for row in rows:
            key = (row['run'], row['idx'])
            status = 'not_reviewed'
            if row['mode'] != 'train':
                status = 'evaluation_excluded'
            elif row['status'] not in ('completed', 'completed_draw'):
                status = 'incomplete_excluded'
            elif key in accepted:
                status = 'review_claim_not_revalidated'
                if check_evidence:
                    try:
                        status = profile_learning_gate(row)['status']
                    except (OSError, ValueError, KeyError, TypeError, IndexError, sqlite3.Error) as error:
                        status = 'evidence_unavailable_or_invalid'
                        issues.append({'episode': row['idx'], 'reason': str(error)})
                if status == 'approved_for_learning':
                    admitted += 1
                    profile = row['profile']
                    if profile not in PROFILES:
                        raise ValueError('Unknown profile in admitted experience')
                    stats = by_context.setdefault(row['context'], {p: {'n': 0, 'reward_sum': 0.0} for p in PROFILES})
                    stats[profile]['n'] += 1
                    stats[profile]['reward_sum'] += row['reward']
            statuses[status] = statuses.get(status, 0) + 1
        return {'schema_version': 1, 'episodes': len(rows),
                'full_review_claims': len(accepted), 'revalidated_learning_episodes': admitted,
                'episode_admission_counts': statuses, 'reviewed_context_statistics': by_context,
                'evidence_issues': issues,
                'ready_for_measured_update': admitted > 0,
                'strategic_improvement': 'Not established by checkpoint or admission counts',
                'checkpoint_contains_evidence_files': False,
                'recovery_requirement': 'Recover exact evidence directories before reusing reviewed statistics; never silently relabel missing evidence as valid'}
    finally:
        db.close()


def snapshot(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source == output:
        raise ValueError('Source and destination must differ')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.learner-', suffix='.sqlite', dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        # Online backup captures a transactionally consistent DB, including WAL.
        src, dest = readonly(source), sqlite3.connect(temporary)
        try:
            started = time.monotonic()
            def progress(status, remaining, total):
                if time.monotonic() - started > 15:
                    raise TimeoutError("Learner snapshot exceeded 15-second budget")
            src.backup(dest, pages=128, sleep=0.01, progress=progress)
            dest.execute('PRAGMA journal_mode=DELETE')
            dest.commit()
        finally:
            dest.close(); src.close()
        report = inspect_model(temporary)
        with temporary.open('rb') as handle:
            os.fsync(handle.fileno())
        checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
        os.link(temporary, output)  # Refuse to overwrite any earlier checkpoint.
        directory_fd = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return {'format': 1, 'model_sha256': checksum, 'model_bytes': output.stat().st_size,
                'readiness': report, 'source_preserved': True,
                'persistence': 'local_only_until_external_save_and_readback',
                'learning_update_performed': False}
    finally:
        temporary.unlink(missing_ok=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--snapshot', type=Path)
    p.add_argument('--report', type=Path, required=True)
    a=p.parse_args()
    if a.report.exists():
        p.error('Existing report retained; allocate a new attempt')
    result=snapshot(a.model,a.snapshot) if a.snapshot else inspect_model(a.model)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
