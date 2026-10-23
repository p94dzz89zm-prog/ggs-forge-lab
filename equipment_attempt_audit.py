"""Reconstruct one refused equip attempt from cost evidence and player snapshots.

This checks observed timing, identity and resource continuity. Unknown strategic
reservations and continuous effects remain explicit; no game certificate results.
"""
import json
from pathlib import Path

COST = 'forge/game/cost/CostPayment.payComputerCosts('

def audit(rows, before, after, *, card_name, oracle_equip_cost):
    if type(oracle_equip_cost) is not int or oracle_equip_cost < 0:
        raise ValueError('Explicit nonnegative Oracle equip cost required')
    state=before['state'];actor=state.get('viewer_id')
    if type(actor) is not int or after['state'].get('viewer_id')!=actor:
        raise ValueError('Missing or changed observing actor')
    states=[state,after['state']]
    for s in states:
        ids=[p.get('id') for p in s['players']]
        if any(type(i) is not int for i in ids) or len(ids)!=len(set(ids)):
            raise ValueError('Ambiguous player identities')
    calls={};failures=[]
    for r in rows:
        if not r.get('hook','').startswith(COST):continue
        cid=r.get('call_id')
        if type(cid) is not int:raise ValueError('Ambiguous payment identity')
        if r['kind']=='engine_call':
            if cid in calls:raise ValueError('Duplicate payment entry')
            calls[cid]=r
        elif r['kind']=='engine_return':
            if cid not in calls:raise ValueError('Unpaired payment return')
            c=calls.pop(cid);a=c.get('receiver',{}).get('ability',{})
            if a.get('source',{}).get('name')==card_name and r.get('result') is False:
                failures.append((c,r,a))
    if calls:raise ValueError('Incomplete payment evidence')
    if len(failures)!=1:raise ValueError('Exactly one refused equipment payment required')
    entry,result,a=failures[0];source=a['source'];cid=source.get('card_id');aid=a.get('ability_id')
    if any(type(i) is not int for i in [cid,aid,a.get('activating_player_id')]):raise ValueError('Ambiguous ability identity')
    if a['activating_player_id']!=actor:raise ValueError('Payment actor differs from snapshot')
    if a.get('api')!='Attach' or a.get('activated') is not True or a.get('spell') is not False:
        raise ValueError('Payment is not an activated attachment')
    selected=before['decision'].get('selected')
    if selected!=f'{cid}:{aid}':raise ValueError('Selection and failed payment disagree')
    for key in ['turn','phase']:
        if entry.get(key)!=state.get(key):raise ValueError('Payment and snapshot context disagree')
    if entry.get('priority_player_id')!=actor or entry.get('turn_player_id')!=actor or state.get('active_player_id')!=actor:
        raise ValueError('Observed equip actor lacks main-turn priority')
    if state['phase'] not in ['MAIN1','MAIN2'] or state.get('stack')!=[]:
        raise ValueError('Observed equip timing is not main phase with empty stack')
    player=next(p for p in state['players'] if p['id']==actor)
    cards=player['battlefield'];equipment=[c for c in cards if c.get('id')==cid]
    if len(equipment)!=1 or equipment[0]['name']!=card_name or 'Equipment' not in equipment[0]['type']:
        raise ValueError('Equipment not uniquely on observed battlefield')
    targets=a.get('direct_targets')
    if not isinstance(targets,list) or len(targets)!=1 or type(targets[0].get('card_id')) is not int:
        raise ValueError('Single direct creature target required')
    tid=targets[0]['card_id'];target=[c for c in cards if c.get('id')==tid]
    if len(target)!=1 or 'Creature' not in target[0]['type'] or target[0].get('controller_id')!=actor:
        raise ValueError('Observed equip target is not a controlled battlefield creature')
    if entry['receiver'].get('base_cost')!='{'+str(oracle_equip_cost)+'}':
        raise ValueError('Base equip cost differs from frozen Oracle cost')
    pools=state.get('public_mana_pools',[]);pool=[p for p in pools if p.get('player_id')==actor]
    if len(pool)!=1:raise ValueError('Missing or ambiguous observed pool')
    if type(pool[0].get('total')) is not int or pool[0]['total']!=len(pool[0].get('units',[])):
        raise ValueError('Observed pool count and units disagree')
    unchanged=state==after['state']
    return dict(payment_call_id=entry['call_id'],turn=state['turn'],actor_id=actor,
        card_id=cid,ability_id=aid,target_card_id=tid,base_equip_cost=oracle_equip_cost,
        observed_main_phase_priority_and_empty_stack=True,
        observed_target_control_and_creature_type=True,floating_mana=pool[0]['total'],
        untapped_observed_lands=[c['id'] for c in cards if 'Land' in c['type'] and not c['tapped']],
        prior_attachment_targets=[c['id'] for c in cards if cid in c.get('attachments',[])],
        observed_snapshots_unchanged=unchanged,payment_succeeded=False,
        limitations=['Player snapshots do not include every hidden or internal state field',
            'Potential lands do not prove mana-source availability or unrestricted payment',
            'Protection, restrictions and continuous effects require independent derivation',
            'Original payment-plan and strategic reservation context absent'],
        root_cause_established=False,rules_approved=False,training_admission=False)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rows');p.add_argument('snapshots');p.add_argument('--card',required=True);p.add_argument('--equip-cost',type=int,required=True);a=p.parse_args()
    snapshots=json.loads(Path(a.snapshots).read_text());selected=[r for r in snapshots if r['state']['phase']=='MAIN1']
    print(json.dumps(audit(json.loads(Path(a.rows).read_text()),*selected,card_name=a.card,oracle_equip_cost=a.equip_cost),indent=2))
