"""Independent continuity of committed mana plans and observed action priority.

Derives unpaid-cost progress from actual unit transitions. Native cost adjustment,
source legality, spending restrictions and priority entitlement derivation remain
unapproved even when all recorded transactions are internally consistent.
"""
from collections import Counter
import json
from pathlib import Path
import re
from mana_unit_audit import check, check_pool_transition, check_rejected_transition

PLAN='forge/ai/ComputerUtilMana.payManaCost('
UNIT='forge/game/mana/ManaPool.tryPayCostWithMana('
EXECUTE='forge/ai/validation/RulesValidationController.playChosenSpellAbility('

def identity(a):
    if not isinstance(a,dict):raise ValueError('Missing payment ability')
    result=(a.get('ability_id'),a.get('source',{}).get('card_id'),a.get('activating_player_id'))
    if any(type(x) is not int for x in result):raise ValueError('Ambiguous payment ability identity')
    return result

def cost(value):
    if not isinstance(value,dict) or not isinstance(value.get('unpaid_shards'),list):return None
    shards=value['unpaid_shards'];generic=value.get('generic')
    if any(not isinstance(x,str) for x in shards) or type(generic) is not int or generic<0:
        raise ValueError('Malformed structured unpaid cost')
    if shards.count('{1}')!=generic:raise ValueError('Generic cost and shards disagree')
    return Counter(shards)

def printed_cost(a):
    """Compare a plain fixed printed cost; never derive modifiers from silence."""
    if a.get('spell') is not True or a.get('alternative_costs') or a.get('optional_costs'):
        return None
    text=a.get('source',{}).get('mana_cost');parts=re.findall(r'\{([^{}]+)\}',text or '')
    if not parts or ''.join('{'+s+'}' for s in parts)!=text:return None
    result=Counter()
    for s in parts:
        if s.isdecimal():result['{1}']+=int(s)
        elif s in 'WUBRGC' and len(s)==1:result['{'+s+'}']+=1
        else:return None
    return +result

def audit_rows(rows):
    active=[];seen=set();counts=Counter();gaps=Counter();transactions=[];finished=False
    for r in rows:
        if finished:raise ValueError('Data after completion marker')
        if r.get('kind')=='engine_tape_complete':
            if active:raise ValueError('Completion with open payment ancestry')
            finished=True;continue
        kind=r.get('kind');hook=r.get('hook','')
        if kind=='engine_call':
            cid=r.get('call_id');parent=r.get('parent_call_id',0)
            if type(cid) is not int or cid in seen or type(parent) is not int or parent!=(active[-1]['entry']['call_id'] if active else 0):
                raise ValueError('Broken call identity or ancestry')
            seen.add(cid);frame={'entry':r,'plan':None}
            if hook.startswith(PLAN):
                args=r.get('arguments',[])
                if type(r.get('speculative')) is not bool or len(args)!=6 or any(type(x) is not bool for x in args[3:]):
                    raise ValueError('Ambiguous mana plan test flags')
                if args[3] is False and r.get('speculative') is False:
                    ident=identity(args[1]);actor=args[2].get('player_id')
                    if type(actor) is not int or actor!=ident[2]:raise ValueError('Mana plan payer differs from ability actor')
                    initial=cost(args[0]);frame['plan']=dict(identity=ident,initial=initial,current=initial,units=0,rejected=0,gaps=[],ability=args[1])
                    counts['committed_mana_plans']+=1
            active.append(frame)
        elif kind=='engine_return':
            if not active or active[-1]['entry']['call_id']!=r.get('call_id'):raise ValueError('Unpaired or out-of-order return')
            frame=active.pop();entry=frame['entry'];args=entry.get('arguments',[])
            if hook!=entry.get('hook'):raise ValueError('Changed return hook')
            if hook.startswith(UNIT):
                if type(entry.get('speculative')) is not bool or len(args)!=4 or type(args[3]) is not bool or type(r.get('result')) is not bool:raise ValueError('Ambiguous mana unit test/result')
                if args[3] is False and entry.get('speculative') is False:
                    plan=next((f['plan'] for f in reversed(active) if f['plan'] is not None),None)
                    if plan is None:gaps['actual_unit_without_committed_plan']+=1;continue
                    if identity(args[0])!=plan['identity']:raise ValueError('Mana unit charged to another ability or payer')
                    after_args=r.get('arguments_after',[])
                    if len(after_args)!=4:raise ValueError('Missing mana unit return arguments')
                    if identity(after_args[0])!=plan['identity'] or after_args[3] is not False:
                        raise ValueError('Mana unit return changed paying ability or test status')
                    before=cost(args[1]);after=cost(after_args[1])
                    if before is None or after is None or plan['current'] is None:
                        plan['gaps'].append('unstructured_cost_progress')
                    elif before!=plan['current']:
                        plan['gaps'].append('unobserved_cost_progress_before_unit')
                    context=entry.get('mana_context',{})
                    if r['result']:
                        issue=check(args[1],after_args[1],args[2],context)
                        pool=check_pool_transition(context.get('pool'),r.get('mana_pool_after'),args[2])
                        if issue:plan['gaps'].append(issue)
                        if pool:plan['gaps'].append(pool)
                        plan['units']+=1;counts['attributed_successful_mana_units']+=1
                    else:
                        issue=check_rejected_transition(args[1],after_args[1],context.get('pool'),r.get('mana_pool_after'))
                        if issue:plan['gaps'].append(issue)
                        plan['rejected']+=1;counts['attributed_rejected_mana_units']+=1
                    plan['current']=after
            if frame['plan'] is not None:
                p=frame['plan'];value=r.get('result');after_args=r.get('arguments_after',[])
                if len(after_args)!=6:raise ValueError('Missing mana plan return arguments')
                if identity(after_args[1])!=p['identity']:
                    raise ValueError('Mana plan return changed paying ability')
                final=cost(after_args[0])
                if value is not None and not isinstance(value,list):raise ValueError('Ambiguous mana plan result')
                success=value is not None
                if success:
                    counts['successful_mana_plans']+=1
                    if final is None:p['gaps'].append('unstructured_final_cost')
                    elif +final:raise ValueError('Successful mana plan left unpaid cost')
                    if final is not None and p['current'] is not None and final!=p['current']:
                        p['gaps'].append('unobserved_cost_progress_at_return')
                    if p['initial'] is None:p['gaps'].append('unstructured_initial_cost')
                    if not p['gaps']:counts['complete_unit_progress_chains']+=1
                else:counts['failed_mana_plans_requires_rollback_review']+=1
                printed=printed_cost(p['ability'])
                relation='not_plain_fixed_spell'
                if printed is not None and p['initial'] is not None:
                    relation='equal' if printed==p['initial'] else 'different_requires_modifier_derivation'
                    counts['printed_to_locked_'+relation]+=1
                gaps.update(p['gaps'])
                transactions.append(dict(call_id=entry['call_id'],turn=entry.get('turn'),phase=entry.get('phase'),ability_id=p['identity'][0],source_card_id=p['identity'][1],actor_id=p['identity'][2],source_name=p['ability']['source'].get('name'),initial_cost_shards=list(p['initial'].elements()) if p['initial'] is not None else None,successful=success,units=p['units'],rejected=p['rejected'],unit_progress_complete=success and not p['gaps'],printed_to_locked_relation=relation,gaps=p['gaps']))
            if hook.startswith(EXECUTE):
                if type(r.get('result')) is not bool:raise ValueError('Ambiguous selected-action result')
                if r['result']:
                    counts['successful_selected_actions']+=1
                    actor=entry.get('actor_id')
                    if type(actor) is not int or type(entry.get('priority_player_id')) is not int:gaps['missing_observed_action_priority']+=1
                    elif actor!=entry['priority_player_id']:raise ValueError('Successful selected action by player without recorded priority')
                    else:counts['observed_action_priority_matches']+=1
    if not finished or active:raise ValueError('Incomplete transaction history')
    return dict(counts=dict(counts),gaps=dict(gaps),transactions=transactions,
        limitations=['Locked total is recorded, not independently derived from all Oracle modifiers',
            'Mana source generation, spending restrictions and non-mana costs unapproved',
            'Priority ownership is observed; full entitlement/pass sequence not derived',
            'Casting targets, timing permissions, zones, combat, triggers and terminal rules unapproved'],
        complete_game_approved=False,rules_approved=False,training_admission=False)

def audit(path):
    with Path(path).open('rb') as f:return audit_rows(json.loads(line) for line in f)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('tape');a=p.parse_args();print(json.dumps(audit(a.tape),indent=2))
