"""Scoped read-only private search/public reveal audit, not whole-game approval."""
import argparse,json
from pathlib import Path
from decision_tape import ZONE_EMPTY
from executable_delta import digest

def card_id(card):return card.get('card_id',card.get('view_id'))

def audit(path,source,turn):
    stack=[];active=None;choices=[];private=None;deliveries=0;public=None
    with Path(path).open() as stream:
        for line in stream:
            row=json.loads(line)
            if row['kind']=='engine_call':
                args=row['arguments'];effect_source=None
                if row['hook'].startswith('forge/game/ability/effects/ChangeZoneEffect.resolve('):effect_source=args[0]['source']['card_id']
                stack.append((row['call_id'],effect_source))
                if active is None and row.get('turn')==turn and row['hook'].endswith(ZONE_EMPTY) and args[0]=='Library' and args[2]['source']['card_id']==source:
                    actor=args[7]['player_id'];ids=[card_id(card) for card in args[3]]
                    if len(ids)!=len(set(ids)):raise ValueError('Duplicate choice domain')
                    reveal=args[4]
                    if not choices:
                        if reveal is None or reveal['owner']['view_id']!=actor:raise ValueError('Missing private search owner')
                        private=[card_id(card) for card in reveal['cards']]
                    elif reveal is not None:raise ValueError('Unexpected repeated private look')
                    active=dict(call_id=row['call_id'],actor=actor,domain=sorted(ids))
                if active is not None and row.get('visibility_operation') in ('delivery','look_specified','reveal_all'):
                    if row.get('entitled_player_ids')!=[active['actor']]:raise ValueError('Unauthorized private library audience')
                    payload=args[0];cards=payload['cards'] if isinstance(payload,dict) else payload
                    if [card_id(card) for card in cards]!=private:raise ValueError('Private library order/domain changed')
                    deliveries+=1
                if len(choices)==2 and row.get('turn')==turn and row.get('visibility_operation')=='reveal_all' and any(owner==source for _,owner in stack):
                    ids=[card_id(card) for card in args[0]]
                    if sorted(ids)==sorted(choice['selected'] for choice in choices):
                        if row.get('entitled_player_ids')!=[0,1,2,3]:raise ValueError('Selected cards not revealed to all four players')
                        if public is not None:raise ValueError('Ambiguous repeated selected-card public reveal')
                        public=ids
            elif row['kind']=='engine_return':
                if not stack or stack.pop()[0]!=row['call_id']:raise ValueError('Unpaired search evidence')
                if active is not None and row['call_id']==active['call_id']:
                    chosen=None if row['result'] is None else card_id(row['result'])
                    if chosen not in active['domain']:raise ValueError('Selected card outside legal offered domain')
                    choices.append(dict(actor=active['actor'],domain=active['domain'],selected=chosen));active=None
    if len(choices)!=2 or deliveries<1 or public is None:raise ValueError('Missing complete private-choice/public-reveal evidence')
    return dict(choices=choices,ordered_private_library=private,private_deliveries=deliveries,public_selected_ids=public,public_audience=[0,1,2,3])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',required=True);p.add_argument('--source',required=True,type=int);p.add_argument('--turn',required=True,type=int);a=p.parse_args()
    if digest(a.original)!=a.original_sha256:raise ValueError('Original evidence hash mismatch')
    original=audit(a.original,a.source,a.turn);actual=audit(a.replay,a.source,a.turn)
    if original!=actual:raise ValueError('Original/replay private-choice/public-reveal evidence diverged')
    print(json.dumps(dict(source_card_id=a.source,turn=a.turn,searcher=actual['choices'][0]['actor'],private_library_cards=len(actual['ordered_private_library']),private_deliveries=actual['private_deliveries'],public_selected_ids=actual['public_selected_ids'],public_audience=actual['public_audience'],original_sha256=a.original_sha256,replay_sha256=digest(a.replay),rules_basis=['CR701.20a/e','CR701.23a-b'],scope='Only two private basic-land selections and subsequent public reveal; moves/shuffle/full state/whole-game legality not certified',rules_approved=False),indent=2))
