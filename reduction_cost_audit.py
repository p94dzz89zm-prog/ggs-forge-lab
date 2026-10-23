"""Independent fixed-cost reduction arithmetic over captured characteristics.

Not a general total-cost or Oracle-characteristic legality certificate.
"""
from collections import Counter
import re

def fixed_cost(text):
    parts=re.findall(r'\{([^{}]+)\}',text or '')
    if not parts or ''.join('{'+s+'}' for s in parts)!=text:raise ValueError('Unsupported fixed mana cost')
    result=Counter()
    for s in parts:
        if s.isdecimal():result['{1}']+=int(s)
        elif len(s)==1 and s in 'WUBRGC':result['{'+s+'}']+=1
        else:raise ValueError('Unsupported variable/hybrid/Phyrexian cost')
    return +result

def reduction(board,actor,mechanic):
    if type(actor) is not int:raise ValueError('Ambiguous actor')
    if mechanic not in {'creatures_on_battlefield','controlled_historic_mana_value'}:raise ValueError('Unsupported reduction mechanic')
    ids=set();contributors=[];total=0
    for c in board:
        cid=c.get('id')
        if type(cid) is not int or cid in ids:raise ValueError('Duplicate or ambiguous permanent')
        ids.add(cid)
        if type(c.get('phased_out')) is not bool or type(c.get('controller_id')) is not int or not isinstance(c.get('type'),str):raise ValueError('Missing characteristics')
        if c['phased_out']:continue
        types=set(re.findall(r'[A-Za-z]+',c['type']))
        if mechanic=='creatures_on_battlefield':contribution=1 if 'Creature' in types else 0
        elif mechanic=='controlled_historic_mana_value':
            contribution=0
            if c['controller_id']==actor and types & {'Artifact','Legendary','Saga'}:
                contribution=0 if c.get('mana_cost')=='no cost' else sum(fixed_cost(c.get('mana_cost')).values())
        else:raise ValueError('Unsupported reduction mechanic')
        if contribution:contributors.append(dict(card_id=cid,name=c.get('name'),contribution=contribution));total+=contribution
    return total,contributors

def derive(base_cost,board,actor,mechanic,*,generic_increase=0,other_generic_reduction=0):
    if any(type(n) is not int or n<0 for n in [generic_increase,other_generic_reduction]):raise ValueError('Invalid cost modifier')
    base=fixed_cost(base_cost);amount,contributors=reduction(board,actor,mechanic)
    result=base.copy();result['{1}']=max(0,base['{1}']+generic_increase-amount-other_generic_reduction)
    return dict(reduction=amount,contributors=contributors,expected_shards=dict(+result),scope='Fixed base plus explicitly supplied generic increases/reductions over recorded characteristics',all_modifiers_proven=False,rules_approved=False)
