"""Streaming, read-only progress diagnosis of partial readiness histories.

Repeated *partial* state is a symptom, never a proof of a priority/rules loop.
No missing timestamps or terminal evidence are inferred from exit status.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path


def summarize(path):
    counts, states, phases = Counter(), Counter(), Counter()
    digest = hashlib.sha256()
    size = 0
    first = last = None
    turns = set()
    previous_turn = None
    with Path(path).open('rb') as stream:
        for sequence, line in enumerate(stream, 1):
            digest.update(line);size += len(line)
            row = json.loads(line)
            if (not isinstance(row, dict) or type(row.get('sequence')) is not int
                    or row['sequence'] != sequence or type(row.get('format')) is not int
                    or row['format'] != 1 or row.get('audience') != 'offline_referee_only'):
                raise ValueError('Invalid readiness envelope')
            if counts['trace_complete']:
                raise ValueError('Rows after trace completion')
            counts[row['kind']] += 1
            if sequence == 1 and row['kind'] != 'trace_begin':
                raise ValueError('Missing trace begin')
            if row['kind'] != 'priority_offer':
                continue
            turn = row['turn']
            if type(turn) is not int or turn < 0 or (previous_turn is not None and turn < previous_turn):
                raise ValueError('Invalid or regressing turn counter')
            previous_turn = turn;turns.add(turn)
            phases[(turn, row['phase'])] += 1
            state = {k: row[k] for k in ('turn', 'phase', 'priority', 'players', 'stack')}
            fingerprint = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            states[fingerprint] += 1
            if first is None:first = row
            last = row
    def player_summary(row):
        return [] if row is None else [{k: p[k] for k in ('id', 'life', 'active', 'library_count')}
            | {'battlefield_count': len(p['battlefield'])} for p in row['players']]
    return dict(source_sha256=digest.hexdigest(), bytes=size, counts=dict(counts),
        turns_with_offers=len(turns), last_offer_turn=None if last is None else last['turn'],
        max_offers_in_turn_phase=max(phases.values(), default=0),
        max_exact_partial_state_repetition=max(states.values(), default=0),
        first_players=player_summary(first), last_players=player_summary(last),
        rules_approved=False, complete_game_approved=False,
        diagnosis='Partial progress observations only; no CPU/IO profile, full state-loop proof or terminal audit')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('readiness')
    args = parser.parse_args()
    print(json.dumps(summarize(args.readiness), indent=2, sort_keys=True))
