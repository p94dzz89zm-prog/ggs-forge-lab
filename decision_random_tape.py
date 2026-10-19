"""Project engine randomness for the supported pure-choice replay prefix only.

Mixed controller actions may execute real game effects. Stop before the first
unsupported decision rather than classifying their random requests as AI work.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def extract(source, source_sha256, decisions, output):
    with decisions.open() as stream:
        rows = [json.loads(line) for line in stream]
    terminal = rows.pop()
    if terminal.get('kind') != 'decision_tape_complete' or terminal['source_sha256'] != source_sha256:
        raise ValueError('Unbound decision input')
    if terminal['decisions'] != len(rows) or [r['index'] for r in rows] != list(range(len(rows))):
        raise ValueError('Decision count/order mismatch')
    pure = {'starting_player', 'mulligan_keep', 'priority_pass', 'play_land', 'plain_hand_permanent_spell',
            'replacement_choice', 'counter_choice', 'color_choice', 'zero_effect_mana'}
    prefix = []
    for row in rows:
        reviewed_selector_only = row.get('decision_type') == 'basic_land_mana' and row.get('random_scope') == 'ComputerUtilMana selector only; actual effect scopes excluded'
        if row['kind'] != 'decision' or (row.get('decision_type') not in pure and not reviewed_selector_only):
            break
        prefix.append(row)
    if len(prefix) == len(rows):
        raise ValueError('Complete game requires additional causal review; prefix projection only')
    boundary = rows[len(prefix)]['source_call_record']
    ranges = {r['source_call_record']: r for r in prefix}
    active = None; kept = []; skipped = 0; checksum = hashlib.sha256(); random_index = 0
    with source.open('rb') as stream:
        for n, line in enumerate(stream, 1):
            checksum.update(line)
            if n >= boundary:
                continue
            row = json.loads(line)
            if n in ranges:
                if active is not None:
                    raise ValueError('Overlapping root ranges')
                active = ranges[n]
            if row['kind'] == 'random_bits':
                random_index += 1
                if row['random_index'] != random_index or type(row['bits']) is not int or not 1 <= row['bits'] <= 32:
                    raise ValueError('Random index/width mismatch')
                value = row['value']; bits = row['bits']
                if type(value) is not int or not (-(1 << 31) <= value < (1 << 31) if bits == 32 else 0 <= value < (1 << bits)):
                    raise ValueError('Random value out of range')
                if active is None:
                    kept.append(dict(kind='engine_random_bits', index=len(kept), bits=bits, value=value,
                                     source_record=n, source_random_index=random_index))
                else:
                    skipped += 1
            if active is not None and n == active['source_return_record']:
                active = None
    if active is not None or checksum.hexdigest() != source_sha256:
        raise ValueError('Unclosed prefix or source checksum mismatch')
    kept.append(dict(kind='engine_random_complete', requests=len(kept), prefix_decisions=len(prefix),
                     next_unsupported_decision=len(prefix), source_sha256=source_sha256,
                     rules_approved=False, full_game_replay=False))
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=output.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            for row in kept:
                stream.write(json.dumps(row) + '\n')
            stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return dict(prefix_decisions=len(prefix), engine_random_requests=len(kept)-1,
                skipped_pure_choice_random_requests=skipped, full_game_replay=False, rules_approved=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True); p.add_argument('--sha256', required=True)
    p.add_argument('--decisions', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(extract(a.source, a.sha256, a.decisions, a.output), indent=2))
