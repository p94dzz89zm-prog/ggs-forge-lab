"""Read-only scoped Partner library-look entitlement audit, not game approval."""
import argparse,json
from pathlib import Path
from decision_tape import ZONE_EMPTY
from executable_delta import digest

def searches(path):
    stack=[];active=None;results=[]
    for line in Path(path).open():
        row=json.loads(line)
        if row['kind']=='engine_call':
            if active is None and row['hook'].endswith(ZONE_EMPTY):
                args=row['arguments'];ability=args[2];name=ability['source']['name']
                if name in ('Frodo, Adventurous Hobbit','Sam, Loyal Attendant'):
                    reveal=args[4];owner=args[7]['player_id']
                    if args[0:2]!=['Hand',['Library']] or args[3]!=[] or args[6] is not True or reveal['owner']['view_id']!=owner or reveal['zones']!=['Library'] or ability['targets']!=[]:raise ValueError('Unsupported empty Partner search context')
                    cards=reveal['cards'];ids=[card['view_id'] for card in cards]
                    if len(ids)!=len(set(ids)) or any(card['owner']['view_id']!=owner or card['zone']!='Library' for card in cards):raise ValueError('Invalid search library ownership/domain')
                    active=dict(call_id=row['call_id'],source_name=name,source_card_id=ability['source']['card_id'],actor_id=owner,library_card_ids=ids,deliveries=0)
            if active is not None and row.get('visibility_operation') in ('delivery','reveal_all','look_specified'):
                if row.get('entitled_player_ids')!=[active['actor_id']]:raise ValueError('Library look disclosed to unauthorized player')
                args=row['arguments'];payload=args[0]
                cards=payload['cards'] if isinstance(payload,dict) else payload
                if [card['view_id'] for card in cards]!=active['library_card_ids']:raise ValueError('Delivered library domain/order differs')
                active['deliveries']+=1
            stack.append(row['call_id'])
        elif row['kind']=='engine_return':
            if not stack or stack.pop()!=row['call_id']:raise ValueError('Unpaired search evidence')
            if active is not None and row['call_id']==active['call_id']:
                if row['result'] is not None or active['deliveries']<1:raise ValueError('Missing look delivery or nonempty choice')
                active.pop('call_id');results.append(active);active=None
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',required=True);a=p.parse_args()
    if digest(a.original)!=a.original_sha256:raise ValueError('Original hash mismatch')
    original=searches(a.original);actual=searches(a.replay)
    if not actual or actual!=original[:len(actual)]:raise ValueError('Partner look evidence differs')
    print(json.dumps(dict(reviewed_searches=[{k:v for k,v in row.items() if k!='library_card_ids'}|dict(library_cards=len(row['library_card_ids'])) for row in actual],
                         original_sha256=a.original_sha256,replay_sha256=digest(a.replay),
                         rules_basis=['CR701.20e','CR701.23a-b','CR702.124j'],rules_url='https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt',
                         scope='Only empty Partner search delivery entitlement and unchanged ordered domain; not full legality or state replay',rules_approved=False),indent=2))
