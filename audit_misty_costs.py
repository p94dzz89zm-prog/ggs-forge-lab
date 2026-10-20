"""Read-only mandatory-cost arithmetic and identity audit; not game approval."""
import argparse,json
from pathlib import Path
from executable_delta import digest

def audit(path,source,turn):
    with Path(path).open() as stream:
        return audit_stream(stream,source,turn)

def audit_stream(stream,source,turn):
    active=None;stack=[];costs=[];life=[];zones=[];success=[];adjustments=[];found=0
    for line in stream:
        row=json.loads(line);hook=row.get('hook','');args=row.get('arguments',[])
        if row['kind']=='engine_call':
            stack.append(row['call_id'])
            if active is None and row.get('turn')==turn and hook.startswith('forge/game/cost/CostPayment.payComputerCosts('):
                receiver=row.get('receiver',{});ability=receiver.get('ability',{})
                if ability.get('source',{}).get('card_id')==source:
                    if receiver.get('base_cost')!='{T}, Pay 1 life, Sacrifice CARDNAME':raise ValueError('Unexpected total cost')
                    active=row['call_id'];found+=1
            if active is not None:
                if '.payAsDecided(' in hook and not hook.startswith('forge/game/cost/CostPartMana.'):
                    if len(args)!=4 or args[2]['source']['card_id']!=source or args[3] is not False:raise ValueError('Cost source/effect mismatch')
                    choice=args[1]
                    if hook.startswith('forge/game/cost/CostTap.'):
                        if choice['count']!=0 or choice['cards']!=[] or args[2]['source']['tapped']:raise ValueError('Invalid tap payment')
                        costs.append('tap')
                    elif hook.startswith('forge/game/cost/CostPayLife.'):
                        if choice['count']!=1 or args[0]['life']<1:raise ValueError('Invalid life payment')
                        costs.append('life1')
                    elif hook.startswith('forge/game/cost/CostPartWithList.'):
                        cards=choice['cards']
                        if row['receiver'].get('cost')!='Sacrifice CARDNAME' or len(cards)!=1 or cards[0]['card_id']!=source or cards[0]['zone']!='Battlefield' or cards[0]['controller_id']!=args[0]['player_id']:raise ValueError('Invalid self sacrifice')
                        costs.append('self_sacrifice')
                    else:raise ValueError('Unsupported nonmana payment')
                    success.append(row['call_id'])
                if hook.startswith('forge/game/Game.fireEvent('):
                    event=args[0]
                    if event.get('record_type')=='GameEventPlayerLivesChanged':life.append(event['oldLives']-event['newLives'])
                    if event.get('record_type')=='GameEventCardChangeZone' and event['card']['view_id']==source:zones.append(event['card']['zone'])
        elif row['kind']=='engine_return':
            if not stack or stack.pop()!=row['call_id']:raise ValueError('Unpaired cost evidence')
            if active is not None:
                if row['call_id'] in success and row['result'] is not True:raise ValueError('Failed native cost payment')
                if hook.startswith('forge/game/cost/CostAdjustment.adjust(Lforge/game/cost/Cost;'):
                    adjustments.append(row['result'])
                if row['call_id']==active:
                    if row['result'] is not True:raise ValueError('Incomplete total cost')
                    active=None
    if found!=1 or active is not None or costs!=['tap','life1','self_sacrifice'] or life!=[1] or zones!=['Graveyard'] or adjustments!=['{T}, Pay 1 life, Sacrifice CARDNAME']:raise ValueError('Missing or discrepant native cost evidence: '+repr((found,costs,life,zones,adjustments)))
    return dict(payments=costs,life_paid=1,self_sacrifice_destination='Graveyard',adjusted_total_cost=adjustments[0],scope='Only exact Misty mandatory costs; priority, search, replacements and full-game legality separately required',rules_approved=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',required=True);p.add_argument('--source',type=int,required=True);p.add_argument('--turn',type=int,required=True);a=p.parse_args()
    if digest(a.original)!=a.original_sha256:raise ValueError('Original checksum mismatch')
    expected=audit(a.original,a.source,a.turn);actual=audit(a.replay,a.source,a.turn)
    if actual!=expected:raise ValueError('Native costs diverged')
    print(json.dumps(dict(actual,original_sha256=a.original_sha256,replay_sha256=digest(a.replay),rules_basis=['CR118.3','CR118.3b','CR601.2h','CR602.2b']),indent=2))
