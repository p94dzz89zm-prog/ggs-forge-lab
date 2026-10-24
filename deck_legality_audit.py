"""Commander construction checks against an external, frozen Oracle snapshot.

Rule logic is independent of Forge. Oracle mirror provenance and historical
as-of validity remain explicit evidence dependencies, never inferred from pass.
"""
from collections import Counter
import re
from certification_inventory import parse_deck

def paper_index(cards):
    index={};playable=[]
    for c in cards:
        if c.get('digital') is True or 'paper' not in c.get('games',[]) or c.get('layout') in {'art_series','token','double_faced_token','emblem'}:continue
        if not c.get('oracle_id'):raise ValueError('Missing canonical Oracle identity')
        name=c['name']
        if name in index and index[name]['oracle_id']!=c['oracle_id']:raise ValueError('Ambiguous canonical paper card name')
        index[name]=c;playable.append(c)
    canonical=set(index)
    for c in playable:
        for name in {f['name'] for f in c.get('card_faces',[])}-canonical:
            prior=index.get(name)
            if prior is not None and prior['oracle_id']!=c['oracle_id']:raise ValueError('Ambiguous paper card name')
            index[name]=c
    return index

def text(card):return '\n'.join([card.get('oracle_text',''),*[f.get('oracle_text','') for f in card.get('card_faces',[])]])

def eligible(c):
    types=c.get('type_line','').split(' // ')[0]
    vehicle=bool(set(re.findall(r'[A-Za-z]+',types)) & {'Vehicle','Spacecraft'}) and isinstance(c.get('power'),str) and isinstance(c.get('toughness'),str)
    return ('Legendary' in types and ('Creature' in types or vehicle)) or 'can be your commander' in text(c).lower()

def partner_pair(a,b):
    at,bt=text(a),text(b)
    pa=re.search(r'Partner with ([^\n(]+)',at);pb=re.search(r'Partner with ([^\n(]+)',bt)
    if pa and pb:return pa[1].strip()==b['name'] and pb[1].strip()==a['name']
    av=re.search(r'(?:^|\n)Partner[—–-]([^\n(]+)',at);bv=re.search(r'(?:^|\n)Partner[—–-]([^\n(]+)',bt)
    if av or bv:return bool(av and bv and av[1].strip()==bv[1].strip())
    return bool(re.search(r'(?:^|\n)Partner(?:\s*\(|\s*$)',at) and re.search(r'(?:^|\n)Partner(?:\s*\(|\s*$)',bt))

def audit_deck(deck_text,cards,ban_snapshot,*,game_date,snapshot_date,identity_index=None):
    deck=parse_deck(deck_text);index=paper_index(cards);issues=[];gaps=[];rows=[];resolved={};counts=Counter()
    if identity_index is not None:
        for alias,canonical in identity_index.names.items():
            if canonical in index:
                if alias in index and index[alias]['oracle_id']!=index[canonical]['oracle_id']:raise ValueError('Reviewed alias conflicts with catalog identity')
                index[alias]=index[canonical]
    for zone,entries in deck.items():
        for name,n in entries.items():
            c=index.get(name)
            if c is None:gaps.append(dict(code='unresolved_card_identity',name=name));continue
            oid=c['oracle_id'];counts[oid]+=n;resolved[oid]=c
            rows.append(dict(deck_name=name,canonical_name=c['name'],oracle_id=oid,printing_id=c.get('id'),zone=zone,count=n,color_identity=c.get('color_identity'),layout=c.get('layout'),released_at=c.get('released_at'),mirror_commander_legality=c.get('legalities',{}).get('commander')))
    commanders=[index[n] for n in deck['Commander'] if n in index]
    for c in commanders:
        if not eligible(c):issues.append(dict(code='commander_not_eligible',name=c['name']))
    if len(commanders)==2 and not partner_pair(*commanders):gaps.append(dict(code='unproved_or_unsupported_commander_pair',names=[c['name'] for c in commanders]))
    identity=set().union(*(set(c.get('color_identity',[])) for c in commanders))
    for oid,c in resolved.items():
        name=c['name'];typ=c.get('type_line','');oracle=text(c);allowed=None
        if re.search(r'\bBasic\b',typ) and re.search(r'\bLand\b',typ):allowed=100
        elif re.search(r'A deck can have any number of cards named',oracle):allowed=100
        elif re.search(r'A deck can have up to',oracle):gaps.append(dict(code='bounded_copy_exception_requires_review',name=name))
        else:allowed=1
        if allowed is not None and counts[oid]>allowed:issues.append(dict(code='singleton_violation',name=name,count=counts[oid]))
        ci=c.get('color_identity')
        if not isinstance(ci,list) or any(x not in 'WUBRG' for x in ci):gaps.append(dict(code='missing_or_malformed_color_identity',name=name))
        elif not set(ci)<=identity:issues.append(dict(code='color_identity_violation',name=name,card_identity=ci,commander_identity=sorted(identity)))
        basic_types=dict(Plains='W',Island='U',Swamp='B',Mountain='R',Forest='G')
        if re.search(r'\bLand\b',typ):
            colors={v for t,v in basic_types.items() if re.search(r'\b'+t+r'\b',typ)}
            if not colors<=identity:issues.append(dict(code='basic_land_type_violation',name=name,land_colors=sorted(colors)))
        if name in ban_snapshot['banned_names']:issues.append(dict(code='official_commander_ban',name=name))
        status=c.get('legalities',{}).get('commander')
        if status not in {'legal','banned'}:issues.append(dict(code='mirror_nonlegal_paper_card',name=name,status=status))
        elif (status=='banned')!=(name in ban_snapshot['banned_names']):gaps.append(dict(code='mirror_primary_banlist_disagreement',name=name,mirror_status=status))
        # The Oracle bulk file may select an upcoming reprint of an existing
        # card. A printing date alone cannot establish first card release.
    if sum(counts.values())!=100:gaps.append(dict(code='not_all_100_cards_resolved',resolved=sum(counts.values())))
    return dict(card_count=100,commanders=[c['name'] for c in commanders],commander_color_identity=sorted(identity),cards=rows,violations=issues,evidence_gaps=gaps,current_snapshot_rules_checks_passed=not issues and not gaps,current_snapshot_date=snapshot_date,historical_game_date=game_date,historical_deck_legality_certified=False,oracle_source='External Scryfall Oracle mirror; complete publisher/as-of verification not established',historical_evidence_gap='Current snapshot is not a historical Oracle/banned-list archive',rules=['903.3','903.4','903.5a-d','702.124','709','712','715'],complete_game_approved=False,training_admission=False)
