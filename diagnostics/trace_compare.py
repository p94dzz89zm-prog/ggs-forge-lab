"""Supplement exact legacy trace checks with phase-scoped combat/damage inventories.

This is a log comparison, not a proof of rules equivalence. Non-combat/damage
records retain their order; only combat participant display order and per-phase
combat/damage record order are ignored. Full combat continuation lines count.
"""
from collections import Counter
import json, re
CATEGORIES = {'Turn', 'Phase', 'Add To Stack', 'Resolve Stack', 'Damage', 'Combat', 'Life'}

def combat_record(line):
    match = re.fullmatch(r'(.+?) assigned (.+) to (attack|block) (.+)\.', line)
    if match:
        actor, participants, action, target = match.groups()
        ids = sorted(map(int, re.findall(r'\((\d+)\)', participants)))
        if ids:
            return json.dumps([actor, action, target, ids])
    return line

def read_games(text):
    games = {}
    legacy, phases = [], []
    ordered, unordered = [], []
    in_combat = False
    count = 0
    def flush():
        nonlocal ordered, unordered
        if ordered or unordered:
            phases.append((tuple(ordered), tuple(sorted(Counter(unordered).items()))))
            ordered, unordered = [], []
    for line in text.splitlines():
        category = line.split(':', 1)[0]
        if category in CATEGORIES:
            legacy.append(line)
            count += 1
            if category in {'Turn', 'Phase'}:
                flush()
                ordered.append(line)
            elif category == 'Combat':
                unordered.append('Combat: ' + combat_record(line.split(': ', 1)[1]))
            elif category == 'Damage':
                unordered.append(line)
            else:
                ordered.append(line)
            in_combat = category == 'Combat'
        elif in_combat and line.startswith('Ai('):
            unordered.append('Combat: ' + combat_record(line))
            count += 1
        else:
            in_combat = False
        if 'DragonMind Result: ' in line:
            game = json.loads(line.split('DragonMind Result: ', 1)[1])
            flush()
            games[game['seed']] = {'legacy': legacy, 'phases': phases, 'count': count, 'game': game}
            legacy, phases, ordered, unordered = [], [], [], []
            count = 0
    return games

def compare(a, b):
    return {'trace_match': a['legacy'] == b['legacy'],
            'phase_inventory_match': a['phases'] == b['phases'],
            'full_tracked_records': a['count'],
            'full_record_count_match': a['count'] == b['count']}
