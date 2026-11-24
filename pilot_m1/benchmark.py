"""Matched position benchmark, stratified by opening. Never scores game strength."""
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from .policy import Hand, Pilot, Policy, fingerprint

SEATS = 4


def configs(rotation, checkpoints, seeds, mode='certification'):
    if type(rotation) is not int or rotation not in range(SEATS) or len(checkpoints)!=4 or len(seeds)!=4:
        raise ValueError('Invalid four-seat allocation')
    return [dict(seat=s,identity=i,seed=seeds[i],mode=mode,checkpoint=checkpoints[i])
            for s in range(SEATS) for i in [(s+rotation)%SEATS]]


def compare(groups, lineups, seeds, split):
    """groups contains one first-look Hand per deck and matched opening block.

    Each lineup can supply the previous, fixed, independently updated or
    historical versions. Compare on the same actor positions across rotations.
    """
    if split not in ('development','heldout') or not groups or not lineups:
        raise ValueError('Missing split, positions or comparison lineups')
    unique = set()
    fingerprint_inputs = []
    for key, hands in groups:
        if key in unique or len(hands)!=4 or any(type(h) is not Hand for h in hands):
            raise ValueError('Duplicate or incomplete opening block')
        unique.add(key)
        fingerprint_inputs.append([key,[asdict(h) for h in hands]])
    reports = {}
    for name, snapshots in lineups.items():
        counts = Counter()
        records = []
        for key, hands in groups:
            for rotation in range(4):
                for cfg in configs(rotation,snapshots,seeds):
                    seat = cfg['seat']
                    offer = dict(game='opening',seat=seat,revision=0,observation=asdict(hands[seat]),
                                 actions=['keep','redraw'])
                    rec = Pilot(**cfg).decide(offer)
                    replay = Pilot(**cfg).decide(offer)
                    if rec != replay:
                        raise ValueError('Nonreproducible decision')
                    choice = rec['selection']['token']
                    if choice not in offer['actions']:
                        raise ValueError('Unoffered choice')
                    counts[choice] += 1
                    counts['scored_actions'] += rec['calculations']['scored_actions']
                    records.append([key,rotation,seat,cfg['identity'],rec['policy'],choice])
        reports[name] = dict(decisions=len(records),reproduced=len(records),counts=dict(counts),
                             policy_sha256=[fingerprint(s) for s in snapshots],records=records)
    return dict(schema=1,split=split,opening_blocks=len(groups),rotations=4,lookahead=0,
                input_sha256=fingerprint(fingerprint_inputs),decision_seeds=list(seeds),lineups=reports,
                independent_games=0,win_rate=None,uncertainty='Descriptive fixture counts; no game sample',
                promotion=False,training_admitted=False)


def demonstration():
    hands = [Hand(1,2,False),Hand(3,1,False),Hand(5,0,True),Hand(6,1,False)]
    initial = Policy().checkpoint()
    return compare([('synthetic-heldout-A',hands)],{'fixed':[initial]*4},
                   [11,19,23,31],'heldout')


if __name__ == '__main__':
    print(json.dumps(demonstration(),indent=2))
