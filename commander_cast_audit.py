"""Derive commander-tax contributions from observed cast origins, not counters.

This establishes a cost contribution and scoped arithmetic comparisons only.
Origin-zone entitlement, all other modifiers, continuous effects and complete
game legality remain independent obligations.
"""
from collections import Counter
import json
from pathlib import Path
from payment_transaction_audit import EXECUTE, PLAN, cost, identity, printed_cost


def audit_rows(rows):
    active=[];seen=set();commanders=None;casts=Counter();counts=Counter()
    gaps=Counter();events=[];finished=False
    for r in rows:
        if finished:raise ValueError('Data after completion marker')
        kind=r.get('kind');hook=r.get('hook','')
        if kind=='engine_tape_complete':
            if active:raise ValueError('Completion with open call ancestry')
            finished=True;continue
        if kind=='engine_call':
            cid=r.get('call_id');parent=r.get('parent_call_id',0)
            if type(cid) is not int or cid in seen or type(parent) is not int or parent!=(active[-1]['entry']['call_id'] if active else 0):
                raise ValueError('Broken call identity or ancestry')
            seen.add(cid);args=r.get('arguments',[])
            event=args[0].get('record_type') if args and isinstance(args[0],dict) else None
            if event=='GameEventGameStarted':
                if commanders is not None or events:raise ValueError('Repeated or late initial state')
                commanders={}
                players=r.get('initial_state',{}).get('players',[])
                if not players:raise ValueError('Missing initial commander identities')
                for p in players:
                    pid=p.get('id')
                    if type(pid) is not int or not isinstance(p.get('Command'),list):raise ValueError('Ambiguous initial player')
                    for c in p['Command']:
                        if c.get('commander') is not True:continue
                        card=c.get('card_id')
                        if type(card) is not int or card in commanders or c.get('owner_id')!=pid or c.get('zone')!='Command':
                            raise ValueError('Ambiguous initial commander identity')
                        commanders[card]=pid
                if not commanders:raise ValueError('Missing initial commanders')
            frame={'entry':r,'execution':None}
            if hook.startswith(EXECUTE):
                if r.get('speculative') is not False or len(args)!=1:raise ValueError('Ambiguous selected execution')
                frame['execution']={'ability':args[0],'plans':[],'events':[]}
            if hook.startswith(PLAN):
                if type(r.get('speculative')) is not bool or len(args)!=6 or type(args[3]) is not bool:
                    raise ValueError('Ambiguous mana-plan test status')
                if r['speculative'] is False and args[3] is False:
                    ex=next((f['execution'] for f in reversed(active) if f['execution']),None)
                    if ex is not None and identity(args[1])==identity(ex['ability']):
                        frame['plan']=(ex,cost(args[0]),cid)
            if event=='GameEventSpellAbilityCast':
                a=r.get('announced_ability',{});src=a.get('source',{})
                if a.get('spell') is True and (src.get('commander') is True or (commanders is not None and src.get('card_id') in commanders)):
                    if r.get('speculative') is not False:raise ValueError('Ambiguous commander announcement')
                    if commanders is None:raise ValueError('Commander cast before initial evidence')
                    aid,card,actor=identity(a)
                    if card not in commanders or src.get('commander') is not True:raise ValueError('Changed commander identity')
                    ex=next((f['execution'] for f in reversed(active) if f['execution']),None)
                    if ex is None or identity(ex['ability'])!=(aid,card,actor):raise ValueError('Commander cast has no matching origin execution')
                    origin=ex['ability'].get('source',{}).get('zone')
                    if not isinstance(origin,str) or origin not in {'Command','Hand','Graveyard','Exile','Library','Battlefield'}:
                        raise ValueError('Missing commander cast origin')
                    execution=next(f['entry'] for f in reversed(active) if f['execution'] is ex)
                    locations=[(p.get('id'),zone) for p in execution.get('execution_state_before',{}).get('players',[]) for zone in ['Command','Hand','Graveyard','Exile','Library','Battlefield'] for c in p.get(zone,[]) if c.get('card_id')==card]
                    if len(locations)!=1 or locations[0][1]!=origin:
                        raise ValueError('Commander origin differs from recorded pre-execution zone')
                    if ex['events']:raise ValueError('Duplicate commander announcement')
                    if origin=='Command' and commanders[card]!=actor:raise ValueError('Command-zone cast by nonowner')
                    prior=casts[actor,card];tax=2*prior if origin=='Command' else 0
                    if origin=='Command':casts[actor,card]+=1
                    counts['commander_spell_announcements']+=1
                    counts['command_origin_casts' if origin=='Command' else 'other_origin_casts']+=1
                    if tax:counts['nonzero_commander_tax_contributions']+=1
                    e=dict(call_id=cid,execution_call_id=next(f['entry']['call_id'] for f in reversed(active) if f['execution'] is ex),turn=r.get('turn'),ability_id=aid,card_id=card,actor_id=actor,name=src.get('name'),origin=origin,prior_command_casts=prior,commander_tax_generic=tax)
                    ex['events'].append(e);events.append(e)
            active.append(frame)
        elif kind=='engine_return':
            if not active or active[-1]['entry']['call_id']!=r.get('call_id'):raise ValueError('Unpaired or out-of-order return')
            frame=active.pop()
            if hook!=frame['entry'].get('hook'):raise ValueError('Changed return hook')
            if 'plan' in frame:
                ex,locked,cid=frame['plan']
                if r.get('result') is not None:
                    if not isinstance(r['result'],list):raise ValueError('Ambiguous plan result')
                    ex['plans'].append((locked,cid))
            ex=frame['execution']
            if ex and ex['events']:
                if r.get('result') is not True:raise ValueError('Announced commander cast has unsuccessful execution')
                e=ex['events'][0];base=printed_cost(ex['ability'])
                if len(ex['plans'])!=1 or ex['plans'][0][0] is None or base is None:
                    e['comparison']='unsupported_or_ambiguous_cost';gaps[e['comparison']]+=1
                else:
                    locked,cid=ex['plans'][0];expected=base.copy();expected['{1}']+=e['commander_tax_generic']
                    e.update(payment_call_id=cid,printed_shards=dict(+base),base_plus_tax_shards=dict(+expected),locked_shards=dict(+locked))
                    e['comparison']='base_plus_tax_equal' if +expected==+locked else 'other_modifiers_or_discrepancy'
                    counts[e['comparison']]+=1
                    if e['comparison']!='base_plus_tax_equal':gaps[e['comparison']]+=1
    if not finished:raise ValueError('Missing complete tape marker')
    if commanders is None:raise ValueError('Missing initial state')
    return dict(counts=dict(counts),gaps=dict(gaps),casts=events,derived_command_casts=[dict(actor_id=a,card_id=c,count=n) for (a,c),n in sorted(casts.items())],rules_approved=False,complete_game_approved=False,training_admission=False,limitations=['Printed costs and observed origins are capture evidence, not independently established zone entitlement or Oracle characteristics.','Equality establishes base-plus-tax arithmetic only; other modifiers and continuous effects are not exhaustively derived.','Mana production, priority, zone causality, stack, combat, triggers, state-based actions and terminal legality need separate audits.'])


def audit(path):
    with Path(path).open('rb') as stream:return audit_rows(json.loads(line) for line in stream)


if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1]),indent=2))
