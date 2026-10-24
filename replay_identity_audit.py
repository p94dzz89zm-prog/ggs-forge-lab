"""Audit live token birth identities. Reports discrepancies; never rewrites evidence."""
import argparse
from collections import Counter
import hashlib,json
from pathlib import Path

TOKEN_EFFECT='forge/game/ability/effects/TokenEffect.resolve(Lforge/game/spellability/SpellAbility;)V'
EVENT='forge/game/Game.fireEvent('

def births(path):
    stack=[];ordinals=Counter();found=[]
    for number,line in enumerate(Path(path).open(),1):
        row=json.loads(line)
        if row['kind']=='engine_call':
            frame=dict(id=row['call_id'],hook=row['hook'])
            if row['hook']==TOKEN_EFFECT:
                ability=row['arguments'][0]
                base=dict(source_card_id=ability['source']['card_id'],parameters=ability['parameters'],turn=row['turn'])
                key=json.dumps(base,sort_keys=True);ordinals[key]+=1
                frame.update(effect=base,effect_ordinal=ordinals[key],birth_count=0)
            stack.append(frame)
            if row['hook'].startswith(EVENT):
                event=row['arguments'][0]
                if event.get('record_type')=='GameEventCardChangeZone' and event.get('from') is None and event.get('to',{}).get('zoneType')=='Battlefield':
                    effects=[f for f in stack if 'effect' in f]
                    if not effects:continue
                    parent=effects[-1];parent['birth_count']+=1;card=event['card']
                    found.append(dict(record=number,engine_card_id=card['view_id'],cause=dict(**parent['effect'],effect_ordinal=parent['effect_ordinal'],birth_ordinal=parent['birth_count']),characteristics={k:card[k] for k in ('name','owner','controller','zone','face_down','power','toughness')}))
        elif row['kind']=='engine_return':
            if not stack or stack[-1]['id']!=row['call_id'] or stack[-1]['hook']!=row['hook']:raise ValueError('Unpaired identity evidence')
            stack.pop()
    return found

def compare(expected,observed):
    if len(observed)>len(expected):raise ValueError('Unexpected additional token birth')
    discrepancies=[];mapping=[];seen_original=set();seen_actual=set()
    for original,replay in zip(expected,observed):
        if original['cause']!=replay['cause'] or original['characteristics']!=replay['characteristics']:raise ValueError('Token birth cause/characteristics diverged; alias forbidden')
        a,b=original['engine_card_id'],replay['engine_card_id']
        if a in seen_original or b in seen_actual:raise ValueError('Duplicate/ambiguous token identity')
        seen_original.add(a);seen_actual.add(b)
        mapping.append(dict(original_card_id=a,replay_card_id=b,cause=original['cause']))
        if a!=b:discrepancies.append(dict(original_card_id=a,replay_card_id=b,original_record=original['record'],replay_record=replay['record']))
    return dict(compared_token_births=len(observed),original_births_not_reached=len(expected)-len(observed),causal_identity_correspondence=mapping,unresolved_engine_id_discrepancies=discrepancies,driver_aliases_installed=False,complete_state_reconstruction=False,rules_approved=False,training_admission=False,scope='Causal identity audit only; no original or replay evidence changed and no mismatched identity silently accepted')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path,required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--replay',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Fresh report required')
    original_hash=hashlib.sha256(a.original.read_bytes()).hexdigest()
    if original_hash!=a.original_sha256:raise ValueError('Original evidence hash mismatch')
    report=compare(births(a.original),births(a.replay));report.update(original_sha256=original_hash,replay_sha256=hashlib.sha256(a.replay.read_bytes()).hexdigest());a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('compared_token_births','unresolved_engine_id_discrepancies','driver_aliases_installed','rules_approved')}))
if __name__=='__main__':main()
