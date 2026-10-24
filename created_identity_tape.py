"""Compile private causal token identities, never game-state outcomes."""
import argparse
import json
from pathlib import Path
from executable_delta import digest
from replay_identity_audit import births

def compile_tape(original, original_hash, decisions, output):
    if digest(original) != original_hash:
        raise ValueError('Original evidence hash mismatch')
    initial = None
    for line in Path(original).open():
        row = json.loads(line)
        if 'initial_state' in row:
            initial = row['initial_state']; break
    if initial is None:
        raise ValueError('Initial state absent')
    ids = []
    for player in initial['players']:
        for zone in player.values():
            if isinstance(zone, list):
                ids.extend(card['card_id'] for card in zone if isinstance(card, dict) and 'card_id' in card)
    entries = births(original)
    original_ids = [entry['engine_card_id'] for entry in entries]
    if len(ids) != len(set(ids)) or len(original_ids) != len(set(original_ids)) or set(ids) & set(original_ids):
        raise ValueError('Ambiguous initial/created identity')
    report = dict(format=1, original_sha256=original_hash, decisions_sha256=digest(decisions),
                  initial_card_ids=ids, births=entries, rules_approved=False)
    with Path(output).open('x') as stream:
        json.dump(report, stream, sort_keys=True, indent=2); stream.write('\n')
    return dict(births=len(entries), initial_cards=len(ids), sha256=digest(output), rules_approved=False)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',required=True,type=Path)
    parser.add_argument('--original-sha256',required=True)
    parser.add_argument('--decisions',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(compile_tape(args.original,args.original_sha256,args.decisions,args.output)))
