"""Extract private root controller choices without dropping unsupported decisions.

Input must be an already sealed referee tape, pinned by its archived SHA256.
This checks extraction structure, not rules legality or admission to learning.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile

CONTROLLERS = ('forge/ai/PlayerControllerAi.', 'forge/ai/bridge/PlayerControllerBridge.',
               'forge/game/player/PlayerController.')
NUMBER = '.chooseNumber(Lforge/game/spellability/SpellAbility;Ljava/lang/String;II)I'
CARDS = '.chooseCardsForEffect(Lforge/game/card/CardCollectionView;Lforge/game/spellability/SpellAbility;Ljava/lang/String;IIZLjava/util/Map;)Lforge/game/card/CardCollectionView;'
PRIORITY = '.chooseSpellAbilityToPlay()Ljava/util/List;'
REPLACEMENT = '.chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;'
COUNTER = '.chooseCounterType(Ljava/util/List;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Ljava/util/Map;)Lforge/game/card/CounterType;'
COLORS = '.chooseColors(Ljava/lang/String;Lforge/game/spellability/SpellAbility;IILforge/card/ColorSet;)Lforge/card/ColorSet;'
PRIORITY_PHASES = {'UPKEEP', 'DRAW', 'MAIN1', 'COMBAT_BEGIN', 'COMBAT_DECLARE_ATTACKERS',
                   'COMBAT_DECLARE_BLOCKERS', 'COMBAT_FIRST_STRIKE_DAMAGE', 'COMBAT_DAMAGE',
                   'COMBAT_END', 'MAIN2', 'END_OF_TURN'}


def choice(hook):
    return hook.startswith(CONTROLLERS) and not any('.' + name + '(' in hook for name in ('reveal', 'tempShowCards', 'endTempShowCards'))


def trait_identity(value):
    return {'trait_type': value['trait_type'], 'source_card_id': value['source']['card_id'],
            'parameters': value['parameters']}


def encode(entry, returned, index, call_line, return_line):
    hook, args = entry['hook'], entry['arguments']
    row = {'kind': 'unsupported_decision', 'index': index, 'hook': hook,
           'actor_id': entry['receiver'].get('player_id'), 'source_call_id': entry['call_id'],
           'source_call_record': call_line, 'source_return_record': return_line}
    if hook.endswith(PRIORITY):
        if args != [] or returned.get('arguments_after') != []:
            row['reason'] = 'priority_argument_mutation'
        elif returned['result'] is not None and returned['result'] != []:
            row['reason'] = 'selected_ability_requires_choices_and_mutations'
        elif entry.get('priority_player_id') != row['actor_id'] or entry['receiver'].get('lost') is not False or entry.get('phase') not in PRIORITY_PHASES:
            row['reason'] = 'priority_entitlement_or_phase_unverified'
        elif entry.get('mana_context', {}).get('pool') != []:
            row['reason'] = 'nonempty_pool_requires_public_mana_announcement'
        else:
            row.update(kind='decision', decision_type='priority_pass',
                       pass_return='null' if returned['result'] is None else 'empty_list',
                       empty_mana_pool=True,
                       context={key: entry[key] for key in ('turn', 'phase', 'priority_player_id', 'turn_player_id')})
        return row
    if hook.endswith((REPLACEMENT, COUNTER, COLORS)):
        try:
            if args != returned.get('arguments_after'):
                raise ValueError('effect_choice_argument_mutation')
            if hook.endswith(REPLACEMENT):
                offered = [trait_identity(item) for item in args[0]]
                selected = trait_identity(returned['result'])
                if len({json.dumps(item, sort_keys=True) for item in offered}) != len(offered) or selected not in offered:
                    raise ValueError('ambiguous_or_unoffered_replacement')
                row.update(kind='decision', decision_type='replacement_choice', available_effects=offered, selected_effect=selected)
            else:
                ability = args[1]
                row['source_ability'] = None if ability is None else str(ability['source']['card_id']) + ':' + str(ability['ability_id'])
                if hook.endswith(COUNTER):
                    offered, selected = args[0], returned['result']
                    if not all(type(item) is str for item in offered) or type(selected) is not str or len(set(offered)) != len(offered) or selected not in offered:
                        raise ValueError('unoffered_or_ambiguous_counter')
                    if not isinstance(args[3], dict) or any(value is not None for value in args[3].values()):
                        raise ValueError('non_null_counter_parameters_need_binding')
                    row.update(kind='decision', decision_type='counter_choice', title=args[2], available_counters=offered, selected_counter=selected, null_parameter_keys=sorted(args[3]))
                else:
                    allowed, selected = args[4], returned['result']
                    if not all(type(text) is str and text and set(text) <= set('WUBRGC') and len(text) == len(set(text)) for text in (allowed, selected)):
                        raise ValueError('unencoded_color_set')
                    min_, max_ = args[2:4]; colors = set(selected) - {'C'}
                    if type(min_) is not int or type(max_) is not int or not min_ <= len(colors) <= max_ or not colors <= set(allowed):
                        raise ValueError('illegal_color_choice')
                    row.update(kind='decision', decision_type='color_choice', title=args[0], min=min_, max=max_, allowed_colors=allowed, selected_colors=selected)
        except (KeyError, TypeError, ValueError) as error:
            row['kind'] = 'unsupported_decision'; row['reason'] = str(error)
        return row
    if not (hook.endswith(NUMBER) or hook.endswith(CARDS)):
        row['reason'] = 'unsupported_hook'
        return row
    if args != returned.get('arguments_after'):
        row['reason'] = 'recorded_argument_mutation_requires_driver_support'
        return row
    try:
        offset = 0 if hook.endswith(NUMBER) else 1
        ability = args[offset]
        binding = None if ability is None else str(ability['source']['card_id']) + ':' + str(ability['ability_id'])
        row.update(source_ability=binding, title=args[offset + 1], min=args[offset + 2], max=args[offset + 3])
        if type(row['min']) is not int or type(row['max']) is not int or type(row['title']) is not str or type(row['actor_id']) is not int:
            raise ValueError('Unencoded prompt/bounds/controller')
        if hook.endswith(NUMBER):
            n = returned['result']
            if type(n) is not int or not row['min'] <= n <= row['max']:
                raise ValueError('Illegal recorded number')
            row['number'] = n
        else:
            available = [c['card_id'] for c in args[0]]
            selected = [c['card_id'] for c in returned['result']]
            optional = args[5]
            if type(optional) is not bool or any(type(c) is not int for c in available + selected):
                raise ValueError('Unencoded card choice')
            if len(set(available)) != len(available) or len(set(selected)) != len(selected) or not set(selected) <= set(available):
                raise ValueError('Invalid or duplicate card choice')
            if len(selected) > row['max'] or (len(selected) < row['min'] and not (optional and not selected)):
                raise ValueError('Illegal recorded card count')
            row.update(available_card_ids=available, selected_card_ids=selected, optional=optional)
        row['kind'] = 'decision'
    except (KeyError, TypeError, ValueError) as error:
        row['reason'] = str(error)
    return row


def extract(source, expected_sha256, output):
    output = Path(output)
    checksum, stack, roots = hashlib.sha256(), [], {}
    count, calls, initial, terminal, records = 0, 0, 0, False, 0
    supported, unsupported = Counter(), Counter()
    fd, temporary = tempfile.mkstemp(dir=output.parent, prefix='.decision-extract-')
    try:
        with os.fdopen(fd, 'w') as result, Path(source).open('rb') as stream:
            for records, line in enumerate(stream, 1):
                checksum.update(line); row = json.loads(line)
                if terminal or row.get('format') != 1 or row.get('audience') != 'offline_referee_only':
                    raise ValueError('Invalid/late referee record')
                kind = row['kind']
                if kind == 'engine_call':
                    calls += 1
                    if row['call_id'] != calls or row.get('parent_call_id', 0) != (stack[-1][0] if stack else 0):
                        raise ValueError('Call sequence/parent gap')
                    is_choice = choice(row['hook'])
                    if is_choice and not row.get('speculative', False) and not any(item[1] for item in stack):
                        roots[row['call_id']] = (row, records)
                    stack.append((row['call_id'], is_choice, row['hook']))
                    initial += 'initial_state' in row
                elif kind == 'engine_return':
                    if not stack or (row['call_id'], row['hook']) != (stack[-1][0], stack[-1][2]):
                        raise ValueError('Unpaired/out-of-order return')
                    stack.pop()
                    if row['call_id'] in roots:
                        entry, start = roots.pop(row['call_id']); decision = encode(entry, row, count, start, records)
                        (supported if decision['kind'] == 'decision' else unsupported)[decision['hook']] += 1
                        result.write(json.dumps(decision, separators=(',', ':')) + '\n'); count += 1
                elif kind == 'engine_tape_complete':
                    if stack or row['calls'] != calls:
                        raise ValueError('Incomplete calls at completion')
                    terminal = True
                elif kind != 'random_bits':
                    raise ValueError('Unknown referee record')
            if not terminal or initial != 1 or stack or roots or checksum.hexdigest() != expected_sha256:
                raise ValueError('Missing initial/completion state or source checksum mismatch')
            result.write(json.dumps({'kind': 'decision_tape_complete', 'decisions': count,
                                     'source_sha256': expected_sha256, 'unsupported_decisions': sum(unsupported.values()),
                                     'rules_approved': False}) + '\n')
            result.flush(); os.fsync(result.fileno())
        os.link(temporary, output)
        directory = os.open(output.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'source_sha256': expected_sha256, 'records': records, 'root_decisions': count,
            'supported': dict(supported), 'unsupported': dict(unsupported),
            'all_root_choices_retained': True, 'full_game_replay': False, 'rules_approved': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(extract(args.source, args.sha256, args.output), indent=2))
