"""Independent opening-zone arithmetic and mulligan declaration ordering.

Derives draw expectations from captured initial library order. Shuffle entropy,
post-shuffle permutations and historical Oracle legality remain prerequisites;
scoped checks never grant complete event or game certification.
"""
from collections import Counter

KEEP='.mulliganKeepHand('

def audit_rows(rows):
    players=None;zones={};known={};owners={};initial_ids=set();pending=set();rejected=set();kept=set();calls={};mulligans={};counts=Counter();gaps=Counter();defects=[];turns=[];draws=Counter();first_priority=None;started=False;initial=None;round_defect=False
    def defect(code,r,**kw):
        defects.append(dict(code=code,turn=r.get('turn'),phase=r.get('phase'),call_id=r.get('call_id'),stream_sequence=r.get('stream_sequence'),**kw))
    for r in rows:
        kind=r.get('kind');hook=r.get('hook','');args=r.get('arguments',[])
        if kind=='engine_call' and KEEP in hook:
            actor=r.get('receiver',{}).get('player_id')
            if actor not in pending or actor in kept or r.get('speculative') is not False:raise ValueError('Invalid mulligan decision actor or round')
            calls[r['call_id']]=actor
        if kind=='engine_return' and KEEP in hook:
            actor=calls.pop(r['call_id'],None);result=r.get('result')
            if actor is None or type(result) is not bool:raise ValueError('Unpaired or untyped mulligan choice')
            pending.remove(actor);counts['mulligan_decisions']+=1
            if result:kept.add(actor)
            else:
                if actor in mulligans:raise ValueError('New mulligan declaration before previous redraw completed')
                rejected.add(actor);counts['mulligan_rejections']+=1;mulligans[actor]=dict(returned=0,redrawn=0,shuffled=False)
            if not pending:
                pending=set(rejected);rejected.clear();round_defect=False
            continue
        if kind!='engine_call' or not args or not isinstance(args[0],dict):continue
        e=args[0];event=e.get('record_type')
        if event=='GameEventGameStarted':
            if initial is not None:raise ValueError('Repeated initial state')
            initial=r;players=r.get('initial_state',{}).get('players',[])
            ids=[p.get('id') for p in players]
            if len(ids)!=4 or len(set(ids))!=4 or any(type(p) is not int for p in ids):raise ValueError('Four distinct initial players required')
            pending=set(ids)
            for p in players:
                pid=p['id'];zones[pid]={};known[pid]=True
                if type(p.get('life')) is not int or p['life']!=40:raise ValueError('Wrong initial life')
                for z in ['Library','Hand','Command','Battlefield','Graveyard','Exile']:
                    zones[pid][z]=[]
                    for c in p.get(z,[]):
                        if c.get('name')=='Commander Effect' and c.get('commander') is False:continue
                        cid=c.get('card_id')
                        if type(cid) is not int or cid in initial_ids or c.get('owner_id')!=pid or c.get('zone')!=z:raise ValueError('Initial card conservation or owner mismatch')
                        initial_ids.add(cid);owners[cid]=pid;zones[pid][z].append(cid)
                        if c.get('commander') is True and z!='Command':raise ValueError('Commander outside starting command zone')
                if sum(map(len,zones[pid].values()))!=100 or zones[pid]['Hand'] or zones[pid]['Battlefield'] or zones[pid]['Graveyard'] or zones[pid]['Exile']:raise ValueError('Malformed initial zones')
            continue
        if initial is None:continue
        if event=='GameEventShuffle':
            pid=e['player']['view_id'];known[pid]=False;gaps['post_shuffle_library_order_unrecorded']+=1
            if not started:
                if pid not in mulligans or mulligans[pid]['returned']!=7:raise ValueError('Mulligan shuffle before complete hand return or declaration')
                mulligans[pid]['shuffled']=True
        if event=='GameEventTurnBegan':
            if not started:
                if kept!=set(zones) or calls or mulligans:raise ValueError('Turn began before all players kept or redraws completed')
                for pid,z in zones.items():
                    if len(z['Hand'])!=7:raise ValueError('Opening hand not seven')
                counts['seven_card_opening_hands']+=4
            started=True;pid=e['turnOwner']['view_id'];turns.append(pid)
            first=initial['arguments'][0]['firstTurn']['view_id'];ids=[p['id'] for p in players];expected=ids[(ids.index(first)+len(turns)-1)%4]
            if pid!=expected:raise ValueError('First-cycle turn order differs from declared starting player')
        if event=='GameEventPlayerPriority' and first_priority is None:
            first_priority=dict(call_id=r['call_id'],turn=r.get('turn'),phase=e.get('phase'),actor=e.get('priority',{}).get('view_id'))
            if not turns or first_priority['actor']!=turns[0] or first_priority['phase']!='UPKEEP':raise ValueError('Initial ordinary priority differs from first-player upkeep')
            counts['initial_priority_observation_matches']+=1
        if event!='GameEventCardChangeZone':continue
        card=e['card'];cid=card.get('view_id');source=e.get('from');target=e.get('to')
        if cid not in owners:
            if source and source.get('zoneType') in ['Library','Hand'] or target and target.get('zoneType') in ['Library','Hand']:gaps['untracked_new_card_in_opening_hand_or_library']+=1
            continue
        if not source or not target:raise ValueError('Missing original-card zone transition')
        origin=source.get('zoneType');dest=target.get('zoneType');srcpid=(source.get('player') or {}).get('view_id');dstpid=(target.get('player') or {}).get('view_id')
        # A shared stack has no ZoneView player. Namespace its physical cards
        # by owner solely for conservation; this does not infer spell control.
        if origin=='Stack' and srcpid is None:srcpid=owners[cid]
        if dest=='Stack' and dstpid is None:dstpid=owners[cid]
        if srcpid not in zones or dstpid not in zones:raise ValueError('Unresolved zone owner')
        before=zones[srcpid].setdefault(origin,[])
        if cid not in before:raise ValueError('Card absent from recorded origin zone')
        if origin=='Library' and dest=='Hand':
            if not started and srcpid in mulligans:
                m=mulligans[srcpid]
                if m['returned']!=7 or not m['shuffled']:raise ValueError('Mulligan redraw before complete return/shuffle')
                m['redrawn']+=1
                if m['redrawn']==7:del mulligans[srcpid]
            if known[srcpid]:
                if not before or before[0]!=cid:raise ValueError('Draw did not take independently expected library top')
                counts['expected_top_card_draws']+=1
            else:gaps['draw_after_unrecorded_shuffle_order']+=1
            if not started:counts['pregame_library_to_hand_moves']+=1
            elif r.get('phase')=='DRAW':
                draws[srcpid]+=1;counts['first_cycle_draw_step_moves']+=1
        if not started and origin=='Hand' and dest=='Library':
            if srcpid in kept:raise ValueError('Kept player returned hand during mulligans')
            if srcpid not in mulligans:raise ValueError('Hand returned without mulligan declaration')
            mulligans[srcpid]['returned']+=1
            # Before all declarations, the first physical mulligan return is
            # the earliest causal violation; later returns share that root.
            if pending and rejected and not round_defect:
                defect('mulligan_performed_before_all_round_declarations',r,actor=srcpid,undeclared_players=sorted(pending),rules='CR103.5');round_defect=True
        before.remove(cid);zones[dstpid].setdefault(dest,[]).append(cid)
        all_ids=[c for p in zones.values() for z in p.values() for c in z]
        if len(all_ids)!=400 or len(set(all_ids))!=400 or set(all_ids)!=initial_ids:raise ValueError('Opening physical card conservation violated')
        counts['physical_card_conservation_transitions']+=1
    if initial is None or not started or len(turns)!=4 or first_priority is None:raise ValueError('Incomplete opening/first-cycle evidence')
    if any(draws[p]!=1 for p in zones):gaps['first_cycle_draw_requires_additional_effect_review']+=1
    gaps['initial_shuffle_entropy_and_starting_player_selection_unproved']+=1
    gaps['historical_deck_oracle_and_opening_action_permissions_unapproved']+=1
    return dict(counts=dict(counts),gaps=dict(gaps),confirmed_sequence_defects=defects,first_cycle_turn_order=turns,first_cycle_draws=dict(draws),first_priority=first_priority,independently_approved_historical_events=0,opening_state_certified=False,complete_game_approved=False,training_admission=False,scope='Captured initial-state premises -> independently calculated zone membership, top-card draws, hand counts and declaration-before-mulligan ordering; not full-game approval')
