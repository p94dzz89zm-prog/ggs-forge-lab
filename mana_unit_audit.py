"""Independent mana-unit pool/color/cost-transition checks, not full cost approval."""
from collections import Counter

COLORS = {'W':1,'U':2,'B':4,'R':8,'G':16,'C':32}


def check(before, after, unit, context):
    if not isinstance(before,dict) or not isinstance(after,dict):
        return 'Legacy unstructured mana cost'
    if unit not in context.get('pool',[]):
        raise ValueError('Spent mana unit absent from recorded pool')
    conversions=context.get('possible_color_uses')
    if not isinstance(conversions,dict) or unit.get('color') not in conversions:
        return 'Missing mana conversion/restriction matrix'
    uses=conversions[unit['color']]
    if unit.get('snow') and context.get('snow_for_color'):
        uses |= 31
    old,new=Counter(before['unpaid_shards']),Counter(after['unpaid_shards'])
    if old['{1}']!=before['generic'] or new['{1}']!=after['generic']:
        raise ValueError('Generic amount and unpaid shards disagree')
    supported=True
    for shard in old:
        symbols=shard.strip('{}').split('/')
        candidates=[]
        if shard=='{1}':
            if uses:candidates.append(Counter())
        elif shard=='{S}':
            if unit.get('snow'):candidates.append(Counter())
        elif all(s in COLORS or s in ('2','P') for s in symbols) and any(s in COLORS for s in symbols):
            if any(uses & COLORS[s] for s in symbols if s in COLORS):candidates.append(Counter())
            if '2' in symbols and uses:candidates.append(Counter({'{1}':1}))
        else:
            supported=False
        for addition in candidates:
            expected=old.copy();expected[shard]-=1;expected+=addition
            if +expected==+new:
                return None
    if not supported:
        return 'Unsupported unpaid mana shard'
    raise ValueError('Recorded mana color cannot produce the recorded cost transition')
