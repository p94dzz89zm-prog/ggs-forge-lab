"""Independent full-stream event consistency, never complete-game certification.

Run writer-receipt and referee-call verification separately. These checks derive
stack order and life continuity from events; they do not take engine approvals
as rules proofs. Missing rule derivations remain explicit limitations.
"""
from collections import Counter
import json
from pathlib import Path

EXECUTE = 'forge/ai/validation/RulesValidationController.playChosenSpellAbility('


def audit(path):
    with Path(path).open('rb') as stream:
        return audit_rows(json.loads(line) for line in stream)


def audit_rows(rows):
    stack, seen_instances, resolved, actions = [], set(), set(), {}
    initial, final, life, counts, gaps = None, None, {}, Counter(), Counter()
    for row in rows:
        if final is not None:
            raise ValueError('Data after terminal history marker')
        if 'initial_state' in row:
            if initial is not None:raise ValueError('Duplicate initial state')
            initial = row['initial_state']['players']
            if any(type(p.get('id')) is not int or type(p.get('life')) is not int for p in initial):
                raise ValueError('Ambiguous initial player identity or life')
            life = {p['id']:p['life'] for p in initial}
            if len(initial)!=4 or len(life)!=4:raise ValueError('Four distinct initial seats required')
        if row.get('kind')=='engine_tape_complete':
            final=row.get('final_state')
            if not isinstance(final,dict) or not isinstance(final.get('players'),list):
                raise ValueError('Missing terminal player state')
            continue
        if row.get('hook','').startswith(EXECUTE):
            if row.get('kind')=='engine_call':
                actions[row['call_id']]=row
            elif row.get('kind')=='engine_return':
                before=actions.pop(row['call_id'],None)
                if before is None:raise ValueError('Unpaired action execution')
                result=row.get('result')
                if type(result) is not bool:
                    gaps['execution_exception_or_unknown_result']+=1
                elif result:
                    counts['successful_action_executions']+=1
                else:
                    counts['refused_action_executions']+=1
                    pairs=[('execution_state_before','execution_state_after'),('execution_mana_before','execution_mana_after')]
                    if any(a not in before or b not in row for a,b in pairs):
                        gaps['missing_refused_action_transition']+=1
                    elif any(before[a]!=row[b] for a,b in pairs):
                        # Mana abilities may legally remain activated (CR733.1).
                        # A changed state needs a substantive rollback review.
                        gaps['changed_refused_action_requires_review']+=1
                    else:counts['unchanged_refused_action_transitions']+=1
        if row.get('kind')!='engine_call' or not row.get('hook','').startswith('forge/game/Game.fireEvent('):continue
        event=row['arguments'][0];kind=event.get('record_type')
        if kind=='GameEventSpellAbilityCast':
            aid=event['sa']['ability_id'];sid=event['si']['stack_instance_id']
            if type(aid) is not int or type(sid) is not int or sid in seen_instances:
                raise ValueError('Invalid or reused stack instance')
            seen_instances.add(sid);stack.append((aid,sid));counts['stack_announcements']+=1
        elif kind=='GameEventSpellResolved':
            aid=event['spell']['ability_id']
            if not stack or stack[-1][0]!=aid:raise ValueError('Resolution did not match top announced stack object')
            sid=stack[-1][1]
            if sid in resolved:raise ValueError('Duplicate resolution event')
            resolved.add(sid);counts['lifo_resolution_checks']+=1
        elif kind=='GameEventSpellRemovedFromStack':
            aid=event['sa']['ability_id'];matches=[i for i,(a,s) in enumerate(stack) if a==aid]
            if len(matches)!=1:raise ValueError('Removed stack identity missing or ambiguous')
            _,sid=stack.pop(matches[0]);counts['stack_removals']+=1
            if sid not in resolved:gaps['removal_without_resolution_requires_effect_review']+=1
        elif kind=='GameEventPlayerLivesChanged':
            pid=event['player']['view_id'];old,new=event['oldLives'],event['newLives']
            if type(old) is not int or type(new) is not int:raise ValueError('Noninteger life event')
            if pid not in life:gaps['life_change_without_initial_anchor']+=1
            elif life[pid]!=old:raise ValueError('Broken life-total event chain')
            life[pid]=new;counts['life_event_continuity_checks']+=1
    if initial is None or final is None or actions:raise ValueError('Incomplete full-game event history')
    players=final['players'];ids={p['id'] for p in players}
    if any(type(p.get('id')) is not int or type(p.get('life')) is not int for p in players):
        raise ValueError('Ambiguous terminal player identity or life')
    if len(ids)!=4 or ids!=set(life) or len(players)!=4:raise ValueError('Terminal seats changed')
    winners=[]
    for p in players:
        if p['life']!=life[p['id']]:raise ValueError('Terminal life differs from event-derived total')
        if any(type(p.get(k)) is not bool for k in ('active','lost','won')):raise ValueError('Ambiguous terminal player status')
        if p['lost'] and p['won']:raise ValueError('Terminal player both won and lost')
        if p['lost']:
            if p['loss_reason']=='LifeReachedZero':
                if p['life']>0:raise ValueError('Life-zero loss at positive life')
                counts['terminal_nonpositive_life_checks']+=1
                gaps['loss_prevention_and_sba_derivation_unverified']+=1
            else:gaps['terminal_loss_reason_requires_rules_review']+=1
        if p['won']:winners.append(p['id'])
    if len(winners)==1:
        if any(not p['lost'] for p in players if p['id']!=winners[0]):
            gaps['alternate_win_requires_rules_review']+=1
        else:counts['last_player_standing_consistency_checks']+=1
    else:gaps['draw_or_shared_win_requires_rules_review']+=1
    return dict(full_stream_consistency_checked=True,counts=dict(counts),review_gaps=dict(gaps),
                stack_objects_remaining_at_terminal=len(stack),
                limitations=['Casting/timing/target legality and complete payment restrictions',
                             'Independently derived priority and responses',
                             'Damage assignment/prevention, trigger causality and layers/replacements',
                             'Full state-based-action/loss-prevention and commander derivation'],
                rules_approved=False,training_admission=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('tape');a=p.parse_args()
    print(json.dumps(audit(a.tape),indent=2,sort_keys=True))
