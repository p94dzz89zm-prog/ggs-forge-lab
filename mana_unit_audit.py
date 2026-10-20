"""Independent mana-unit pool/color/cost-transition checks, not full cost approval."""
from collections import Counter
import json

COLORS = {'W':1,'U':2,'B':4,'R':8,'G':16,'C':32}


def check_rejected_transition(before, after, pool_before, pool_after):
    """A refused tryPayCostWithMana unit must not consume resources.

    This is the single-unit API contract, not rollback certification for an
    entire failed spell or activation. Legacy missing evidence is a gap.
    """
    if not isinstance(before, dict) or not isinstance(after, dict):
        return 'Missing rejected mana cost transition snapshot'
    if pool_before is None or pool_after is None:
        return 'Missing rejected mana pool transition snapshot'
    if not isinstance(pool_before, list) or not isinstance(pool_after, list):
        raise ValueError('Malformed rejected mana pool transition snapshot')
    # Preserve multiplicity and every recorded restriction; pool order is not
    # resource identity. Never treat equal-looking units as a set.
    def units(pool):
        for unit in pool:
            if (not isinstance(unit, dict) or unit.get('color') not in COLORS
                    or type(unit.get('source_card_id')) is not int
                    or type(unit.get('snow')) is not bool):
                raise ValueError('Malformed rejected mana unit snapshot')
        return Counter(json.dumps(unit, sort_keys=True, allow_nan=False) for unit in pool)
    if units(pool_before) != units(pool_after):
        raise ValueError('Rejected mana payment changed the recorded pool')
    if json.dumps(before, sort_keys=True, allow_nan=False) != json.dumps(after, sort_keys=True, allow_nan=False):
        raise ValueError('Rejected mana payment changed the unpaid cost')
    return None


def check_pool_transition(before, after, unit):
    """A successful actual unit payment removes exactly that unit (CR118.3a).

    Equal-looking units are a multiset, not a set. This checks recorded resource
    conservation, not whether a mana source or spending restriction was legal.
    Missing snapshots remain an explicit coverage gap for older evidence.
    """
    if before is None or after is None:
        return 'Missing mana pool transition snapshot'
    if not isinstance(before, list) or not isinstance(after, list):
        raise ValueError('Malformed mana pool transition snapshot')

    def key(value):
        if not isinstance(value, dict) or value.get('color') not in COLORS:
            raise ValueError('Malformed mana unit snapshot')
        if type(value.get('source_card_id')) is not int or type(value.get('snow')) is not bool:
            raise ValueError('Ambiguous mana unit identity or snow status')
        return json.dumps(value, sort_keys=True, allow_nan=False)

    old, new = Counter(map(key, before)), Counter(map(key, after))
    spent = key(unit)
    if old[spent] < 1:
        raise ValueError('Spent mana unit absent from pool transition snapshot')
    old[spent] -= 1
    if +old != new:
        raise ValueError('Successful payment did not remove exactly one recorded mana unit')
    return None


def check(before, after, unit, context):
    if not isinstance(before,dict) or not isinstance(after,dict):
        return 'Legacy unstructured mana cost'
    if unit not in context.get('pool',[]):
        raise ValueError('Spent mana unit absent from recorded pool')
    conversions=context.get('possible_color_uses')
    if not isinstance(conversions,dict) or unit.get('color') not in conversions:
        return 'Missing mana conversion/restriction matrix'
    uses=conversions[unit['color']]
    # Only the six recorded mana bits are meaningful. Python negative integers
    # have infinitely many leading set bits and would otherwise pay any color.
    if type(uses) is not int or uses < 0 or uses & ~63:
        raise ValueError('Invalid mana conversion bitmask')
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
