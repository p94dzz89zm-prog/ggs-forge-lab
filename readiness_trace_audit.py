"""Receipt-bound causal readiness protocol audit, not complete rules approval."""
import hashlib
import json
from pathlib import Path


def audit(path):
    path = Path(path)
    receipt = json.loads(Path(str(path)+'.receipt.json').read_text())
    if type(receipt.get('records')) is not int or type(receipt.get('bytes')) is not int:
        raise ValueError('Ambiguous readiness receipt counters')
    digest = hashlib.sha256()
    size = count = 0
    def rows(stream):
        nonlocal size, count
        for line in stream:
            digest.update(line)
            size += len(line)
            count += 1
            yield json.loads(line)
    with path.open('rb') as stream:
        result = audit_rows(rows(stream))
    if receipt.get('bytes') != size or receipt.get('sha256') != digest.hexdigest():
        raise ValueError('Readiness receipt mismatch')
    if receipt['records'] != count:
        raise ValueError('Readiness record count mismatch')
    return result


def audit_rows(rows):
    stage = None
    ready = None
    complete = False
    windows = sba = triggers = offers = early = 0
    def state(row):
        keys = ('turn', 'phase', 'priority', 'players', 'stack', 'snapshot_scope')
        if any(k not in row for k in keys):
            raise ValueError('Incomplete readiness snapshot')
        return {k: row[k] for k in keys}
    for i, row in enumerate(rows, 1):
        if complete or not isinstance(row, dict) or type(row.get('format')) is not int or row.get('format') != 1 or row.get('audience') != 'offline_referee_only':
            raise ValueError('Invalid readiness envelope or data after completion')
        if type(row.get('sequence')) is not int or row['sequence'] != i or type(row.get('result')) is not bool:
            raise ValueError('Ambiguous readiness sequence/result')
        snapshot = state(row)
        kind = row.get('kind')
        if i == 1:
            if kind != 'trace_begin':
                raise ValueError('Missing readiness trace begin')
            continue
        if kind == 'readiness_enter':
            if stage is not None:
                raise ValueError('Overlapping readiness windows')
            stage, ready = 'sba', None
        elif kind == 'sba_return':
            if stage != 'sba':
                raise ValueError('SBA return outside expected readiness phase')
            sba += 1
            stage = 'triggers'
        elif kind == 'triggers_return':
            if stage != 'triggers':
                raise ValueError('Triggers staged before SBA check')
            triggers += 1
            stage = 'sba' if row['result'] else 'exit'
        elif kind == 'readiness_exit':
            if row['result']:
                if stage != 'triggers':
                    raise ValueError('Unexpected early readiness exit')
                early += 1 # Game-over derivation not established by this snapshot.
                ready = None
            else:
                if stage != 'exit':
                    raise ValueError('Readiness exited before SBA/trigger fixed point')
                windows += 1
                ready = snapshot
            stage = None
        elif kind == 'priority_offer':
            if stage is not None or ready is None or ready != snapshot:
                raise ValueError('Priority offered without matching completed readiness state')
            offers += 1
            ready = None
        elif kind == 'trace_complete':
            if stage is not None:
                raise ValueError('Trace sealed during incomplete readiness')
            complete = True
        else:
            raise ValueError('Unknown readiness event')
    if not complete:
        raise ValueError('Unsealed readiness trace')
    return dict(protocol_verified=True, readiness_windows=windows, sba_returns=sba,
                trigger_staging_returns=triggers, priority_offers=offers,
                unverified_game_over_exits=early, snapshot_scope='partial diagnostic',
                complete_game=False, rules_approved=False, training_admission=False)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path)
    print(json.dumps(audit(p.parse_args().trace), indent=2))
