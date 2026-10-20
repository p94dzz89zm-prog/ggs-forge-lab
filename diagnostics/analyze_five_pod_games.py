"""Extract per-game outcomes, commander timing and actions from audited pod batches."""
import argparse, collections, hashlib, json, re
from pathlib import Path


def summarize(run, include_private_hands=False, expected_games=5):
    summaries=json.loads((run/'summary.json').read_text())
    assert len(summaries)==expected_games and all(s['status'] in ('completed','completed_draw') for s in summaries)
    seats=summaries[0]['seats']; variant=summaries[0]['variant']; ggs_seat=seats.index(variant)
    assert all(s['seats']==seats and s['variant']==variant for s in summaries)
    logs=list(dict.fromkeys(run/s['log'] for s in summaries)); games=[]; lines=[]
    for line in (line for log in logs for line in log.read_text().splitlines()):
        lines.append(line)
        if line.startswith('DragonMind Result: '):
            result=json.loads(line.split(': ',1)[1]); player=f'Ai({ggs_seat+1})-'+variant
            turn=0; phase=''; own=[]; casts=[]; triggers=collections.Counter(); actions=[]; damage=collections.defaultdict(collections.Counter)
            for entry in lines:
                m=re.match(r'Turn: Turn (\d+) \((.*)\)',entry)
                if m:
                    turn=int(m[1])
                    if m[2]==player: own.append(turn)
                if entry.startswith('Phase: '):phase=entry.split(': ',1)[1]
                if entry.startswith('Add To Stack: '+player):
                    actions.append({'turn':turn,'phase':phase,'line':entry})
                    if entry=='Add To Stack: '+player+' cast Goro-Goro and Satoru':
                        casts.append({'global_turn':turn,'own_turn':own.index(turn)+1 if turn in own else None,'phase':phase})
                    if ' triggered ' in entry:triggers[entry.split(' triggered ',1)[1].split(' targeting ',1)[0]]+=1
                m=re.match(r'Damage: (.+?) \((\d+)\) deals (\d+) (non-combat|combat) damage to (.+)\.',entry)
                if m:damage[m[1]][m[5]]+=int(m[3])
            outcome=next((entry.split(' has ',1)[1] for entry in lines if entry.startswith('Game Outcome: '+player+' has ')),None)
            games.append({**result,'own_turns':own,'commander_casts':casts,'trigger_counts':dict(triggers),'stack_actions':actions,'logged_damage_by_source':{k:dict(v) for k,v in damage.items()},'ggs_outcome_reason':outcome})
            lines=[]
    assert [g['seed'] for g in games]==[s['seed'] for s in summaries]
    # Priority streams append across games. Verify the segments against the requested summaries.
    priority={}; evaluation={}; hands=[collections.Counter() for _ in games]; openings=[None for _ in games]
    seed_to_segment={g['seed']:i for i,g in enumerate(games)}
    board_peaks=[{'permanents':0,'creatures':0,'turn':None} for _ in games]
    own_board_peaks=[0 for _ in games]
    absent_viewer_rows=[0 for _ in games]
    combat_turns=[{} for _ in games]; ninjutsu=[collections.Counter() for _ in games]
    for file in sorted((run/'audit').rglob('seat-*.jsonl')):
        count=0; segment=seed_to_segment[int(re.search(r'seeds(\d+)-',file.parent.name)[1])]; initial_segment=segment; previous=0
        for line in file.open():
            row=json.loads(line);state=row['state']; turn=state['turn']
            if turn<previous:segment+=1
            previous=turn;count+=1
            if file.name==f'seat-{ggs_seat}.jsonl':
                me=next((p for p in state['players'] if p['id']==ggs_seat),None)
                if me is None:
                    absent_viewer_rows[segment]+=1
                    continue
                own_board_peaks[segment]=max(own_board_peaks[segment],sum('Creature' in c.get('type','') for c in me['battlefield']))
                permanents=sum(len(p['battlefield']) for p in state['players'])
                creatures=sum('Creature' in c.get('type','') for p in state['players'] for c in p['battlefield'])
                if creatures>board_peaks[segment]['creatures']:
                    board_peaks[segment]={'permanents':permanents,'creatures':creatures,'turn':turn}
                if state.get('active_player_id')==ggs_seat and state['phase'] in ('COMBAT_DECLARE_BLOCKERS','COMBAT_FIRST_STRIKE_DAMAGE') and 'combat' in state:
                    own_cards={c['id']:c for c in me['battlefield']}
                    attacks=[a for a in state['combat']['attackers'] if a['attacker_id'] in own_cards]
                    fresh=[a for a in attacks if own_cards[a['attacker_id']].get('entered_this_turn',False)]
                    ggs=any(c.get('name')=='Goro-Goro and Satoru' for c in me['battlefield'])
                    prior=combat_turns[segment].get(turn,{})
                    combat_turns[segment][turn]={'phase':state['phase'],'ggs_named_creature_present':ggs,
                        'attackers':len(attacks),'fresh_attackers':len(fresh),'fresh_unblocked_attackers':sum(a['unblocked'] for a in fresh),
                        'ggs_named_creature_seen':prior.get('ggs_named_creature_seen',False) or ggs,
                        'fresh_attack_with_ggs_seen':prior.get('fresh_attack_with_ggs_seen',False) or (ggs and bool(fresh)),
                        'fresh_unblocked_with_ggs_seen':prior.get('fresh_unblocked_with_ggs_seen',False) or (ggs and any(a['unblocked'] for a in fresh))}
                if openings[segment] is None:openings[segment]=[c['name'] for c in me.get('hand',[])]
                for card in me.get('hand',[]):hands[segment][card['name']]+=1
        expected_end=seed_to_segment[int(re.search(r'-(\d+)$',file.parent.name)[1])]
        assert segment==expected_end,(file,segment,expected_end)
        priority[file.parent.name+'/'+file.stem]=count
    for file in sorted((run/'audit').rglob('evaluation-seat-*.jsonl')):
        decisions=collections.Counter();count=0
        segment=seed_to_segment[int(re.search(r'seeds(\d+)-',file.parent.name)[1])];previous=0
        for line in file.open():
            row=json.loads(line);count+=1
            if include_private_hands:decisions[row['decision']]+=1
            if row['turn']<previous:segment+=1
            previous=row['turn']
            if file.name==f'evaluation-seat-{ggs_seat}.jsonl' and row.get('is_ninjutsu',False):
                decision=row['decision']
                category='paid_return' if decision.startswith('GgsNinjutsu:payReturn=') else 'no_damage_plan' if decision=='GgsNinjutsu:noDamagePlan' else 'plan_scored' if decision.startswith('GgsNinjutsu:score=') else decision
                if category not in {'paid_return','no_damage_plan','plan_scored','CantPlaySa','CantPlayAi','CantAfford','WillPlay','CantPlayTargets','CantPlayCost'}:category='other'
                ninjutsu[segment][category]+=1
        evaluation[file.parent.name+'/'+file.stem]={'rows':count}
        if include_private_hands:evaluation[file.parent.name+'/'+file.stem]['decisions']=dict(decisions)
    for i,g in enumerate(games):
        g['peak_observed_creature_board']=board_peaks[i]
        g['peak_observed_ggs_creatures']=own_board_peaks[i]
        g['excluded_priority_snapshots_without_ggs']=absent_viewer_rows[i]
        g['observed_combat_turns']=combat_turns[i];g['ninjutsu_evaluation_counts']=dict(ninjutsu[i])
        if include_private_hands:
            g['opening_hand']=openings[i];g['hand_snapshot_occurrences']=dict(hands[i])
    return {'games':games,'summary':summaries,'performance':json.loads((run/'performance.json').read_text()),'metadata':json.loads((run/'metadata.json').read_text()),'log_sha256':{log.name:hashlib.sha256(log.read_bytes()).hexdigest() for log in logs},'priority_counts':priority,'evaluation_counts':evaluation,'audit_bytes':sum(p.stat().st_size for p in (run/'audit').rglob('*.jsonl'))}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_directory',type=Path);p.add_argument('--expected-games',type=int,default=5);p.add_argument('--include-private-hands',action='store_true',help='Include private hands and raw evaluation decision strings for local analysis; omit for public reports');a=p.parse_args()
    result={name:summarize(a.run_directory/name,a.include_private_hands,a.expected_games) for name in ['apex','layered']}
    (a.run_directory/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,deck in result.items():
        for g in deck['games']:print(name,g['seed'],g['winner'],g['engine_ms'],g['last_logged_turn'],g['commander_casts'])
