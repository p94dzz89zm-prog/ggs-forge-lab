"""Validate private engine call evidence. This is not a Magic rules oracle.

No row from this omniscient tape is a permitted pilot observation or training
example. Sealed writer receipts must be checked separately before this reader.
"""
import collections
import json
from pathlib import Path
from priority_pass_audit import PriorityPassAudit, CHOICE


def inspect(path, *, require_initial=True):
    with Path(path).open('rb') as stream:
        return _inspect(stream, require_initial=require_initial)


def _inspect(stream, *, require_initial):
    pending, entered, returned = {}, set(), set()
    records = 0
    mana_verified, mana_unsupported = 0, collections.Counter()
    pool_verified, pool_unsupported = 0, collections.Counter()
    initial, terminal, visibility, paid, failed, random = [], [], [], 0, 0, 0
    unknown = collections.Counter()
    priority = PriorityPassAudit()

    def gaps(value):
        if isinstance(value, dict):
            if 'unencoded' in value:
                unknown[value['unencoded']] += 1
            for child in value.values():
                gaps(child)
        elif isinstance(value, list):
            for child in value:
                gaps(child)

    for line in stream:
        row = json.loads(line)
        records += 1
        if not isinstance(row, dict) or type(row.get('format')) is not int or row.get('format') != 1 or row.get('audience') != 'offline_referee_only':
            raise ValueError('Missing private referee schema/audience')
        kind = row.get('kind')
        if terminal:
            raise ValueError('Data after referee completion')
        priority.next_row(row)
        if kind == 'engine_call':
            call = row['call_id']
            if type(call) is not int or call != len(entered) + 1:
                raise ValueError('Duplicate or missing engine call')
            parent = row.get('parent_call_id', 0)
            if type(parent) is not int or parent != (next(reversed(pending)) if pending else 0):
                raise ValueError('Invalid parent call order')
            if not isinstance(row.get('hook'), str) or not row['hook']:
                raise ValueError('Missing engine call hook')
            if 'speculative' in row and type(row['speculative']) is not bool:
                raise ValueError('Ambiguous speculative status')
            pending[call] = row
            entered.add(call)
            if 'initial_state' in row:
                initial.append(row['initial_state'])
            if 'visibility_operation' in row:
                entitled = row.get('entitled_player_ids')
                if not isinstance(entitled, list) or len(set(entitled)) != len(entitled) or any(type(p) is not int for p in entitled):
                    raise ValueError('Missing or ambiguous reveal audience')
                visibility.append(row)
        elif kind == 'engine_return':
            call = row['call_id']
            if type(call) is not int or call not in pending or call in returned or call != next(reversed(pending)):
                raise ValueError('Missing, duplicate or unordered engine return')
            entry = pending.pop(call)
            if row.get('hook') != entry['hook']:
                raise ValueError('Return hook changed')
            returned.add(call)
            priority.returned(entry, row, nested_priority=any(
                p.get('hook', '').endswith(CHOICE) for p in pending.values()))
            if 'ManaPool.tryPayCostWithMana(' in row['hook']:
                args = entry['arguments']
                if len(args) != 4 or type(args[3]) is not bool or type(row.get('result')) is not bool:
                    raise ValueError('Ambiguous mana payment/test status')
                if not args[3] and not entry.get('speculative', False):
                    if row['result'] is True:
                        from mana_unit_audit import check
                        issue=check(args[1],row['arguments_after'][1],args[2],entry.get('mana_context',{}))
                        if issue:mana_unsupported[issue]+=1
                        else:mana_verified+=1
                        from mana_unit_audit import check_pool_transition
                        issue=check_pool_transition(entry.get('mana_context',{}).get('pool'),
                                                    row.get('mana_pool_after'), args[2])
                        if issue:pool_unsupported[issue]+=1
                        else:pool_verified+=1
                    paid += row['result'] is True
                    failed += row['result'] is False
        elif kind == 'random_bits':
            bits, value = row.get('bits'), row.get('value')
            if type(bits) is not int or not 1 <= bits <= 32 or type(value) is not int or not (-2**31 <= value < 2**31):
                raise ValueError('Invalid random bits')
            if bits < 32 and not 0 <= value < 2**bits:
                raise ValueError('Random value outside bit range')
            if type(row.get('random_index')) is not int or row.get('random_index') != random + 1:
                raise ValueError('Random tape sequence gap')
            random += 1
        elif kind == 'engine_tape_complete':
            if pending or type(row.get('calls')) is not int or row.get('calls') != len(entered):
                raise ValueError('Unfinished engine calls')
            terminal.append(row)
        else:
            raise ValueError('Unknown referee row kind')
        gaps(row)
    if not terminal or pending:
        raise ValueError('Incomplete referee tape')
    if len(initial) > 1 or (require_initial and len(initial) != 1):
        raise ValueError('Missing or ambiguous recorded initial state')
    player_ids = set()
    if initial:
        players = initial[0].get('players', [])
        if any(type(p.get('id')) is not int for p in players):
            raise ValueError('Invalid initial player identity')
        player_ids = {p['id'] for p in players}
        if len(player_ids) != len(players):
            raise ValueError('Duplicate initial player identity')
        for player in players:
            if 'Library' not in player or 'Hand' not in player or 'Command' not in player:
                raise ValueError('Missing initial ordered zones')
    for row in visibility:
        audience = set(row['entitled_player_ids'])
        if initial and not audience <= player_ids:
            raise ValueError('Reveal to unregistered player')
        if row['visibility_operation'] == 'reveal_all' and not audience:
            raise ValueError('Empty public reveal audience')
    return {**priority.report(), 'integrity_structure_passed': True, 'records': records, 'calls': len(entered),
            'initial_states': len(initial), 'registered_players': len(player_ids),
            'visibility_events': len(visibility), 'actual_mana_units_paid': paid,
            'failed_mana_unit_attempts': failed, 'random_requests': random,
            'unencoded_types': dict(unknown), 'mana_unit_transition_checks':mana_verified, 'mana_unit_transition_gaps':dict(mana_unsupported), 'rules_approved': False,
            'mana_pool_transition_checks':pool_verified, 'mana_pool_transition_gaps':dict(pool_unsupported),
            'replay_status': 'Not established by tape inspection', 'training_admission': False}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('tape', type=Path)
    print(json.dumps(inspect(p.parse_args().tape), indent=2))
