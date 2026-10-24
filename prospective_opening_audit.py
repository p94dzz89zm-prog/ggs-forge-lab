"""Independent Java-RNG/permutation and opening-prefix checks, not game approval."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


class JavaRandom:
    def __init__(self, seed): self.state = (seed ^ 0x5DEECE66D) & ((1 << 48)-1)
    def bits(self, count):
        if type(count) is not int or not 1 <= count <= 32: raise ValueError('Invalid RNG bit request')
        self.state = (self.state * 0x5DEECE66D + 11) & ((1 << 48)-1)
        value = self.state >> (48-count)
        return value-(1 << 32) if count == 32 and value >= 1 << 31 else value


def bounded(requests, bound):
    if bound <= 0: raise ValueError('Invalid random bound')
    while True:
        try: count, bits = next(requests)
        except StopIteration: raise ValueError('Missing shuffle RNG request') from None
        if count != 31 or not 0 <= bits < 1 << 31: raise ValueError('Wrong nextInt bit request')
        if bound & (bound-1) == 0: return bound*bits >> 31
        value = bits % bound
        if bits-value+(bound-1) < 1 << 31: return value


def permutation(order, requests):
    out = list(order); iterator = iter(requests)
    for size in range(len(out), 1, -1):
        pick = bounded(iterator, size); out[size-1], out[pick] = out[pick], out[size-1]
    if list(iterator): raise ValueError('Unexplained RNG within shuffle')
    return out


def snapshot_objects(state):
    result = {}; references = []
    physical = {'Hand','Library','Graveyard','Battlefield','Exile','Command','Stack','Sideboard','Ante'}
    for player in state['players']:
        for zone, cards in player.items():
            if not isinstance(cards,list): continue
            if zone == 'Flashback': references.extend(cards); continue
            if zone not in physical and cards: raise ValueError('Unsupported auxiliary zone/view: '+zone)
            for card in cards:
                if card['id'] in result: raise ValueError('Duplicate object identity in physical zones')
                result[card['id']] = (card['name'],card['owner'],card['commander'])
    for card in references:
        if result.get(card['id']) != (card['name'],card['owner'],card['commander']):
            raise ValueError('Unbound Flashback playable-view reference')
    return result


def audit(rows, seed):
    rng = JavaRandom(seed); random = []; stack = []; initial = None; first = None
    shuffles = {}; shuffle_checks = 0; decision_checks = 0; hand_checks = 0; participants = []; declarations = []
    def players(state):
        seats = {p['id']: p for p in state['players']}
        if len(seats) != 4 or len(state['players']) != 4: raise ValueError('Four distinct players required')
        return seats
    def objects(state):
        players(state)
        return snapshot_objects(state)
    for sequence, row in enumerate(rows, 1):
        if row.get('stream_sequence') != sequence: raise ValueError('Missing/reordered opening record')
        if row.get('rules_approved') is not False: raise ValueError('Unsupported approval claim')
        kind = row['kind']
        if 'state' in row:
            identities = objects(row['state'])
            if initial is None:
                initial = identities
                if any(p['life'] != 40 for p in players(row['state']).values()): raise ValueError('Wrong starting life')
            if identities != initial: raise ValueError('Opening object conservation/identity changed')
        if kind == 'opening_random_bits':
            if row['random_index'] != len(random)+1 or rng.bits(row['bits']) != row['value']:
                raise ValueError('Seeded random stream mismatch')
            random.append((row['bits'], row['value'])); continue
        if row['random_index'] != len(random): raise ValueError('Random counter mismatch')
        if kind == 'opening_call':
            hook = row['hook']
            if hook == 'shuffle' and participants and len(declarations) != len(participants):
                raise ValueError('Redraw before all mulligan declarations')
            if hook == 'mulligans':
                if first is None or row['first_player_id'] != first: raise ValueError('Unbound starting player')
                seats = players(row['state']); order = list(seats); offset = order.index(first)
                participants = order[offset:]+order[:offset]
                for player, state in seats.items():
                    expected = shuffles.get(player)
                    if expected is None: raise ValueError('Initial shuffle missing')
                    if Counter(c['id'] for c in state['Hand']) != Counter(expected[:7]) or [c['id'] for c in state['Library']] != expected[7:]:
                        raise ValueError('Opening draw differs from shuffled library')
                    hand_checks += 1
            if hook == 'mulligan_decision':
                if len(declarations) == len(participants):
                    participants = [p for p, keep in declarations if not keep]; declarations = []
                if not participants or row['player_id'] != participants[len(declarations)]:
                    raise ValueError('Mulligan decision order/kept player changed')
            stack.append(dict(row=row, generated=None))
        elif kind == 'shuffle_generated':
            if not stack or stack[-1]['row']['hook'] != 'shuffle': raise ValueError('Unbound permutation')
            frame = stack[-1]; before = frame['row']; player = before['player_id']
            if row['player_id'] != player or frame['generated'] is not None: raise ValueError('Permutation owner/duplicate')
            order = [c['id'] for c in players(before['state'])[player]['Library']]
            expected = permutation(order, random[before['random_index']:row['random_index']])
            if expected != row['order']: raise ValueError('Shuffle permutation mismatch')
            frame['generated'] = expected; shuffle_checks += 1
        elif kind == 'opening_return':
            if not stack or stack[-1]['row']['call_id'] != row['call_id'] or stack[-1]['row']['hook'] != row['hook']:
                raise ValueError('Unpaired opening return')
            frame = stack.pop(); before = frame['row']; hook = row['hook']
            if hook == 'shuffle':
                player = before['player_id']; actual = [c['id'] for c in players(row['state'])[player]['Library']]
                if frame['generated'] is None or actual != frame['generated']: raise ValueError('Post-shuffle controller alteration')
                shuffles[player] = actual
            if hook == 'starting_player_choice':
                order = list(players(before['state']))
                if len(random) != 1 or order[bounded(iter(random),4)] != before['player_id']:
                    raise ValueError('Unsupported/noninitial chooser selection')
                if row['result'] not in order: raise ValueError('Illegal starting-player choice')
                first = row['result']
            if hook == 'starting_player_selection' and row['result'] != first: raise ValueError('Starting selection result mismatch')
            if hook == 'mulligan_decision':
                if type(row['result']) is not bool: raise ValueError('Invalid mulligan declaration')
                declarations.append((before['player_id'],row['result'])); decision_checks += 1
            if hook == 'mulligans' and len(declarations) != len(participants):
                raise ValueError('Incomplete round declarations')
        else: raise ValueError('Unknown opening record')
    if stack or hand_checks != 4 or first is None: raise ValueError('Incomplete opening prefix')
    return dict(rng_requests_verified=len(random),shuffle_permutations_verified=shuffle_checks,
                opening_hands_derived=hand_checks,mulligan_declarations_observed=decision_checks,
                object_identities_conserved=len(initial),starting_player_id=first,
                independently_approved_game_actions=0,opening_state_certified=False,complete_game_certified=False,
                limitations=['Scoped setup transcript only; canonical deck binding and complete pregame-action/first-turn evidence still required',
                             'General mulligan redraw/bottom state causality not derived here; native service controls remain separate',
                             'Initial List-based chooser protocol only; special starting-player effects unsupported'])


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('tape',type=Path);p.add_argument('--seed',type=int,required=True);a=p.parse_args()
    result=audit([json.loads(line) for line in a.tape.open()],a.seed)
    result['input_sha256']=hashlib.sha256(a.tape.read_bytes()).hexdigest();print(json.dumps(result,indent=2))
