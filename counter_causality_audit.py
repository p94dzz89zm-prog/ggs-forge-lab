"""Derive counter-removal event causality, never card or whole-game legality.

Uses object identities, live call ancestry and stack snapshots, not descriptions
or card names. The engine's CounterEffect label is evidence to correlate, not an
independent proof that Oracle permits the effect, target or destination.
"""
from collections import Counter
import json
from pathlib import Path

EVENT = 'forge/game/Game.fireEvent('
RESOLVE = 'forge/game/zone/MagicStack.resolveStack('
COUNTER = 'forge/game/ability/effects/CounterEffect.resolve('


def integer(value):
    if type(value) is not int:
        raise ValueError('Ambiguous object identity')
    return value


def audit_rows(rows):
    active, stack, seen, resolved, stack_ids = {}, [], set(), set(), set()
    contexts, links, gaps, counts = {}, [], Counter(), Counter()
    initial = terminal = False
    sequence = 0

    def ancestor(row, prefix):
        parent = row.get('parent_call_id', 0)
        visited = set()
        while parent:
            if parent in visited or parent not in active:
                raise ValueError('Broken active call ancestry')
            visited.add(parent)
            item = active[parent]
            if item.get('hook', '').startswith(prefix):
                return parent
            parent = item.get('parent_call_id', 0)
        return None

    def identity(sa):
        return integer(sa['ability_id']), integer(sa['source']['card_id'])

    for row in rows:
        if terminal:
            raise ValueError('Data after terminal marker')
        sequence += 1
        if integer(row.get('stream_sequence')) != sequence:
            raise ValueError('Stream sequence gap or reorder')
        if 'initial_state' in row:
            if initial:
                raise ValueError('Duplicate initial state')
            initial = True
        if row.get('kind') == 'engine_tape_complete':
            if active:
                raise ValueError('Terminal marker with open calls')
            terminal = True
            continue
        kind, hook = row.get('kind'), row.get('hook', '')
        if kind == 'engine_call':
            cid = integer(row['call_id'])
            if cid in seen:
                raise ValueError('Reused call identity')
            seen.add(cid)
            # Validate ancestry before registering the current frame.
            ancestor(row, 'never_matches')
            active[cid] = row
            if hook.startswith(RESOLVE):
                snapshot = row.get('receiver')
                if not isinstance(snapshot, list):
                    raise ValueError('Missing resolution stack snapshot')
                observed = [(integer(s['ability']['ability_id']), integer(s['stack_instance_id'])) for s in snapshot]
                if observed != [(s['aid'], s['sid']) for s in reversed(stack)]:
                    raise ValueError('Resolution snapshot differs from event-derived stack')
                counts['resolution_stack_snapshots'] += 1
            if hook.startswith(COUNTER):
                counts['counter_effect_calls'] += 1
                sa = row['arguments'][0]
                aid, card = identity(sa)
                resolver = ancestor(row, RESOLVE)
                if resolver is None or not stack or stack[-1]['aid'] != aid or stack[-1]['card'] != card:
                    raise ValueError('Counter effect is not the active top stack object')
                if row.get('speculative') is not False:
                    raise ValueError('Counter effect lacks non-speculative evidence')
                targets = sa.get('direct_targets')
                if not isinstance(targets, list):
                    gaps['counter_direct_targets_missing'] += 1
                    targets = []
                target_ids = []
                for target in targets:
                    if 'ability_id' not in target:
                        gaps['unsupported_counter_target_kind'] += 1
                        continue
                    target_id = identity(target)
                    if target_id[0] == aid:
                        raise ValueError('Counter effect targets itself')
                    target_ids.append(target_id)
                if len(target_ids) != len(set(target_ids)):
                    raise ValueError('Ambiguous duplicate direct target')
                contexts[cid] = dict(effect=aid, targets=target_ids, removals=[], resolver=resolver)
            if not hook.startswith(EVENT):
                continue
            event = row['arguments'][0]
            tag = event.get('record_type')
            if tag == 'GameEventSpellAbilityCast':
                sa = event['sa']
                aid, sid = integer(sa['ability_id']), integer(event['si']['stack_instance_id'])
                if sid in stack_ids or any(s['aid'] == aid for s in stack):
                    raise ValueError('Ambiguous active stack identity')
                stack_ids.add(sid)
                source = sa['source']
                stack.append(dict(aid=aid, sid=sid, card=integer(source['view_id']),
                                  owner=integer(source['owner']['view_id'])))
            elif tag == 'GameEventSpellResolved':
                aid = integer(event['spell']['ability_id'])
                if not stack or stack[-1]['aid'] != aid or stack[-1]['sid'] in resolved:
                    raise ValueError('Wrong or duplicate resolution')
                resolved.add(stack[-1]['sid'])
            elif tag == 'GameEventSpellRemovedFromStack':
                sa = event['sa']; aid = integer(sa['ability_id'])
                matches = [s for s in stack if s['aid'] == aid]
                if len(matches) != 1 or matches[0]['card'] != integer(sa['source']['view_id']):
                    raise ValueError('Removal identity differs from announced object')
                target = matches[0]
                if target['sid'] not in resolved:
                    counts['unresolved_stack_removals'] += 1
                    ctxid = ancestor(row, COUNTER)
                    if ctxid is None:
                        gaps['unresolved_removal_without_counter_ancestry'] += 1
                    else:
                        ctx = contexts[ctxid]
                        if (aid, target['card']) not in ctx['targets']:
                            if ctx['targets']:
                                raise ValueError('Removed object is not a direct counter target')
                            gaps['counter_removal_without_structured_target'] += 1
                        else:
                            ctx['removals'].append(dict(**target, removal_sequence=row['stream_sequence'], zone=None))
                stack.remove(target)
            elif tag == 'GameEventCardChangeZone':
                ctxid = ancestor(row, COUNTER)
                if ctxid is None:
                    continue
                event_card = integer(event['card']['view_id'])
                for target in contexts[ctxid]['removals']:
                    if target['card'] != event_card:
                        continue
                    if target['zone'] is not None or event['from']['zoneType'] != 'Stack':
                        raise ValueError('Counter departure zone inconsistent or duplicated')
                    destination = event['to']['zoneType']
                    if destination == 'Graveyard':
                        if integer(event['to']['player']['view_id']) != target['owner']:
                            raise ValueError('Countered spell sent to another owner graveyard')
                    else:
                        gaps['counter_destination_requires_replacement_review'] += 1
                    target['zone'] = destination
                    target['zone_sequence'] = row['stream_sequence']
        elif kind == 'engine_return':
            cid = integer(row['call_id'])
            entry = active.pop(cid, None)
            if entry is None or entry['hook'] != hook:
                raise ValueError('Unpaired or mismatched return')
            if any(x.get('parent_call_id') == cid for x in active.values()):
                raise ValueError('Return with live child calls')
            if cid in contexts:
                ctx = contexts.pop(cid)
                # Void success is null. Instrumented exceptional exits can put
                # a serialized Throwable in result rather than an error field.
                if 'error' in row or row.get('result') is not None:
                    gaps['counter_effect_exception'] += 1
                    continue
                for target in ctx['removals']:
                    if target['zone'] is None:
                        gaps['counter_target_departure_missing'] += 1
                    else:
                        links.append(dict(counter_ability_id=ctx['effect'], counter_call_id=cid,
                                          resolver_call_id=ctx['resolver'], **target))
    if not initial or not terminal or active or contexts:
        raise ValueError('Incomplete full-stream counter evidence')
    return dict(full_stream_checked=True, records=sequence, counts=dict(counts), causal_links=links,
                review_gaps=dict(gaps), stack_objects_remaining_at_terminal=len(stack),
                limitations=['Engine effect labels are not independently derived Oracle behavior',
                             'Target characteristics, restrictions, counter prevention and replacement effects unverified',
                             'Casting, payments, priority, combat, triggers, SBAs and terminal legality unverified'],
                rules_approved=False, training_admission=False)


def audit(path):
    with Path(path).open('rb') as stream:
        return audit_rows(json.loads(line) for line in stream)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tape')
    print(json.dumps(audit(parser.parse_args().tape), indent=2, sort_keys=True))
