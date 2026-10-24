"""Scoped private look and search-choice audit, independent of replay execution."""
import argparse,json
from pathlib import Path
from decision_tape import ZONE_EMPTY
from executable_delta import digest

def audit(path,source,turn,require_lineage=False):
    stack=[];active=None;found=[];lineage=None
    with Path(path).open() as stream:
        for line in stream:
            row=json.loads(line);hook=row.get('hook','')
            if row['kind']=='engine_call':
                stack.append(row['call_id']);args=row['arguments']
                if active is None and row.get('turn')==turn and hook.endswith(ZONE_EMPTY) and args[2]['source']['card_id']==source:
                    if args[:2]!=['Battlefield',['Library']] or args[6] is not True or args[2]['source']['zone']!='Graveyard':raise ValueError('Search source/destination differs')
                    actor=args[7]['player_id'];reveal=args[4];private=[c['view_id'] for c in reveal['cards']];domain=sorted(c['card_id'] for c in args[3])
                    if reveal['owner']['view_id']!=actor or reveal['zones']!=['Library'] or len(private)!=len(set(private)) or len(domain)!=len(set(domain)) or not set(domain)<=set(private):raise ValueError('Invalid search entitlement/domain')
                    if require_lineage:
                        ability=args[2]
                        if not ability.get('native_original_distinct_instance') or ability.get('native_original_source_card_id')!=source or not isinstance(ability.get('native_original_ability_id'),int):raise ValueError('Missing native stack-copy lineage')
                        lineage=ability['native_original_ability_id']
                    active=dict(id=row['call_id'],actor=actor,private=private,domain=domain,deliveries=0)
                if active is not None and row.get('visibility_operation') in ('delivery','look_specified','reveal_all'):
                    if row.get('entitled_player_ids')!=[active['actor']]:raise ValueError('Unauthorized private look')
                    payload=args[0];cards=payload['cards'] if isinstance(payload,dict) else payload
                    if [c.get('card_id',c.get('view_id')) for c in cards]!=active['private']:raise ValueError('Changed private library order')
                    active['deliveries']+=1
            elif row['kind']=='engine_return':
                if not stack or stack.pop()!=row['call_id']:raise ValueError('Unpaired search calls')
                if active is not None and row['call_id']==active['id']:
                    selected=None if row['result'] is None else row['result']['card_id']
                    if selected is not None and selected not in active['domain']:raise ValueError('Invalid selected card')
                    if active['deliveries']<1:raise ValueError('Missing actual private delivery')
                    active.pop('id');active['selected']=selected;found.append(active);active=None
    if len(found)!=1 or active is not None:raise ValueError('Incomplete/ambiguous Misty search')
    return found[0],lineage

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',required=True);p.add_argument('--source',type=int,required=True);p.add_argument('--turn',type=int,required=True);a=p.parse_args()
    if digest(a.original)!=a.original_sha256:raise ValueError('Original hash mismatch')
    expected,_=audit(a.original,a.source,a.turn);actual,lineage=audit(a.replay,a.source,a.turn,True)
    if expected!=actual:raise ValueError('Private look/choice differs')
    print(json.dumps(dict(searcher=actual['actor'],private_library_cards=len(actual['private']),private_deliveries=actual['deliveries'],eligible_card_ids=actual['domain'],selected_card_id=actual['selected'],native_original_ability_id=lineage,replay_sha256=digest(a.replay),scope='Only private look, choice membership and native lineage metadata; land replacement/shuffle/full legality separately required',rules_approved=False),indent=2))
