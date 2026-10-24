"""Fail-closed certification inventory, distinct from simulator success.

Records earliest unresolved prerequisites and event-anchored audit obligations.
An obligation is not a confirmed rules defect or an independent root cause.
"""
from collections import Counter
import re

OBLIGATIONS={
 'opening_draws_mulligans':('GameEventCardChangeZone','CR103,903.6-7','Derive opening draws and mulligans from frozen library/hand transitions and recorded choices.'),
 'priority_turn_structure':('GameEventPlayerPriority','CR117,500','Derive APNAP response windows and consecutive passes from state transitions, not recorded holder alone.'),
 'land_plays':('GameEventLandPlayed','CR305,614','Derive land-play allowance, timing and enters-tapped replacements.'),
 'casting_costs_targets':('GameEventSpellAbilityCast','CR601-602','Derive permissions, targets, all cost modifiers and source/spending restrictions.'),
 'stack_effects':('GameEventSpellResolved','CR608','Derive resolved effects from Oracle instructions and independently established targets/state.'),
 'combat_damage':('GameEventAttackersDeclared','CR508-510,615','Derive attackers, blockers, assignment, prevention and resulting damage.'),
 'triggers_replacements_layers':('GameEventSpellAbilityCast','CR603,613-616','Distinguish triggered/activated/spell announcements; derive trigger causes, APNAP and replacements.'),
 'zones_commander_identity':('GameEventCardChangeZone','CR400.7,903.9','Derive zones, new object identity and commander replacement/SBA choices.'),
 'state_based_actions_terminal':('GameEventGameOutcome','CR104,704,800.4','Derive every elimination and game end including prevention and player-owned object removal.')}

def parse_deck(text):
    section=None;result={'Main':Counter(),'Commander':Counter()}
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        if line.startswith('[') and line.endswith(']'):section=line[1:-1];continue
        if section not in result:continue
        m=re.fullmatch(r'([1-9][0-9]*) (.+)',line)
        if not m:raise ValueError('Unparsed deck entry')
        result[section][m[2]]+=int(m[1])
    if sum(result['Main'].values())+sum(result['Commander'].values())!=100:raise ValueError('Deck does not contain exactly 100 cards')
    if sum(result['Commander'].values()) not in [1,2]:raise ValueError('Invalid commander count')
    return result

def initial_decks(initial,deck_texts,identity_index=None):
    players=initial.get('initial_state',{}).get('players',[])
    if len(players)!=4 or len(deck_texts)!=4:raise ValueError('Four initial seats and frozen decks required')
    ids=[p.get('id') for p in players]
    if any(type(x) is not int for x in ids) or len(set(ids))!=4:raise ValueError('Ambiguous initial seats')
    seen=set();reports=[]
    for p,text in zip(players,deck_texts):
        deck=parse_deck(text);observed={'Main':Counter(),'Commander':Counter()};effect_count=0
        if p.get('life')!=40 or type(p.get('life')) is not int:raise ValueError('Incorrect initial life')
        for zone in ['Command','Library','Hand']:
            if not isinstance(p.get(zone),list):raise ValueError('Missing initial zone')
            for c in p[zone]:
                cid=c.get('card_id')
                if type(cid) is not int or cid in seen:raise ValueError('Repeated physical initial card identity')
                seen.add(cid)
                if c.get('owner_id')!=p['id'] or c.get('zone')!=zone:raise ValueError('Initial card owner or zone mismatch')
                if zone=='Command' and c.get('name')=='Commander Effect' and c.get('commander') is False:
                    effect_count+=1;continue
                if type(c.get('commander')) is not bool:raise ValueError('Missing commander designation')
                observed['Commander' if c['commander'] else 'Main'][c.get('name')]+=1
        if effect_count!=1 or sum(observed['Main'].values())+sum(observed['Commander'].values())!=100:raise ValueError('Incorrect physical deck cardinality or command effect')
        if any(p.get(z) for z in ['Battlefield','Graveyard','Exile','Stack']):raise ValueError('Unexpected occupied starting zone')
        bindings=[]
        if identity_index is not None:
            for z in observed:
                observed[z],a=identity_index.normalize(observed[z]);deck[z],b=identity_index.normalize(deck[z]);bindings.extend(dict(zone=z,side=side,**x) for side,rows in [('captured',a),('deck',b)] for x in rows)
        differences={z:dict(captured_only=dict(observed[z]-deck[z]),deck_only=dict(deck[z]-observed[z])) for z in observed if observed[z]!=deck[z]}
        reports.append(dict(player_id=p['id'],physical_cards=100,commanders=sum(deck['Commander'].values()),initial_life=40,identity_multiset_matches=not differences,unresolved_name_bindings=differences,reviewed_name_bindings=bindings,identity_manifest_sha256=identity_index.sha256 if identity_index else None,oracle_format_legality_approved=False))
    return reports

def inventory(inspection,deck_texts,identity_index=None):
    if inspection.get('receipt_verified') is not True or inspection.get('open_calls')!=0 or inspection.get('structural_gaps') or not inspection.get('complete'):
        raise ValueError('Incomplete or unanchored history')
    initial=inspection.get('initial')
    if not isinstance(initial,dict):raise ValueError('Missing initial capture')
    setup=initial_decks(initial,deck_texts,identity_index);seed=inspection['seed']
    anchor=dict(turn=initial.get('turn'),phase=initial.get('phase'),player_id=None,call_id=initial.get('call_id'),stream_sequence=initial.get('stream_sequence'),event='GameEventGameStarted')
    block=dict(id=str(seed)+':oracle-deck-legality',root_cause_family='independent_oracle_legality_evidence',classification='audit_limitation',severity='critical',status='unresolved',blocks_certification=True,anchor=anchor,state_reference='initial.initial_state.players and frozen inputs/*.dck',rules=['CR903.3-5','CR103'],evidence='100 physical cards per seat; unresolved exact-name bindings are retained explicitly. Engine-only deck conformance does not independently prove Oracle identities, color identity, singleton exceptions, commander eligibility/partner or effective format legality.',smallest_reproduction='Run initial_decks against the frozen GameStarted state and four deck files; then require a frozen authoritative identity/format dataset before claiming full legality.',required_fix='Resolve recorded/deck-name differences using authoritative full-card identities, not name splitting; freeze effective legality data and independently validate every deck restriction and commander pairing.',downstream_actions_affected=inspection['event_counts'].get('GameEventSpellAbilityCast',0),downstream_count_basis='Recorded stack announcements exposed to an unapproved setup; not separate root defects')
    if all(p['identity_multiset_matches'] for p in setup):
        block['evidence']='Captured initial card identity multisets match frozen deck entries under the explicitly supplied reviewed identity manifest. Full Oracle characteristics, color identity, singleton exceptions, commander eligibility/partner and effective format legality remain unapproved.'
        block['required_fix']='Freeze authoritative full-card characteristics and effective legality data; independently validate color identity, singleton exceptions, commander eligibility and pairing across every frozen deck.'
    blockers=[block];cfg=inspection['config']
    if cfg.get('commander_damage') is not False or type(cfg.get('free_seven_mulligans')) is not int or cfg['free_seven_mulligans']<3:
        blockers.append(dict(id=str(seed)+':house-profile',root_cause_family='historical_profile_mismatch',classification='configuration_mismatch',severity='critical',status='unresolved',blocks_certification=True,anchor=anchor,evidence=dict(commander_damage=cfg.get('commander_damage'),free_seven_mulligans=cfg.get('free_seven_mulligans')),required_fix='Retain historical game under its actual profile; it cannot be relabeled as a house-rule game. Use separately authorized frozen house-profile gameplay.',smallest_reproduction='Compare frozen config with 40life/no commander damage/at least3 full-seven reshuffles.'))
    obligations=[]
    for scope,(kind,rules,work) in OBLIGATIONS.items():
        event=inspection['first_events'].get(kind)
        obligations.append(dict(scope=scope,status='not_independently_derived',blocks_certification=True,classification='audit_limitation' if event else 'missing_applicability_evidence',earliest_observed_event=event,anchor_is_proof=False,rules=rules,required_fix=work,smallest_reproduction='Extract the anchored event and its causal predecessor state into a deterministic rules fixture; preserve missing predecessor evidence as a gap.',root_cause_family='full_transition_derivation_incomplete'))
    return dict(format=1,seed=seed,raw_sha256=inspection['raw_sha256'],raw_records=inspection['records'],source_commit=inspection['source_commit'],history_receipt_verified=True,initial_structure=setup,root_blockers=blockers,coverage_obligations=obligations,earliest_unresolved=block['id'],candidate_profile='house' if len(blockers)==1 else 'historical_nonhouse',complete_game_approved=False,training_admission=False,limitations=['Event counts and captured terminal state do not prove causality.','Coverage obligations are not confirmed engine defects and are not counted as separate root causes.'])
