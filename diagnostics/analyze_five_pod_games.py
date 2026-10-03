"""Extract per-game outcomes, commander timing and actions from audited pod batches."""
import argparse, collections, hashlib, json, re
from pathlib import Path


def summarize(run, include_private_hands=False):
    summaries=json.loads((run/'summary.json').read_text())
    assert len(summaries)==5 and all(s['status']=='completed' for s in summaries)
    logs=list(dict.fromkeys(run/s['log'] for s in summaries)); games=[]; lines=[]
    for line in (line for log in logs for line in log.read_text().splitlines()):
        lines.append(line)
        if line.startswith('DragonMind Result: '):
            result=json.loads(line.split(': ',1)[1]); player='Ai(1)-'+summaries[0]['variant']
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
            games.append({**result,'own_turns':own,'commander_casts':casts,'trigger_counts':dict(triggers),'stack_actions':actions,'logged_damage_by_source':{k:dict(v) for k,v in damage.items()}})
            lines=[]
    assert [g['seed'] for g in games]==[s['seed'] for s in summaries]
    # Priority streams append across games. Completed games reset turn numbers; verify exactly five segments.
    priority={}; evaluation={}; hands=[collections.Counter() for _ in games]; openings=[None for _ in games]
    seed_to_segment={g['seed']:i for i,g in enumerate(games)}
    board_peaks=[{'permanents':0,'creatures':0,'turn':None} for _ in games]
    for file in sorted((run/'audit').rglob('seat-*.jsonl')):
        count=0; segment=seed_to_segment[int(re.search(r'seeds(\d+)-',file.parent.name)[1])]; initial_segment=segment; previous=0
        for line in file.open():
            row=json.loads(line);state=row['state']; turn=state['turn']
            if turn<previous:segment+=1
            previous=turn;count+=1
            if file.name=='seat-0.jsonl':
                me=next(p for p in state['players'] if p['id']==0)
                permanents=sum(len(p['battlefield']) for p in state['players'])
                creatures=sum('Creature' in c.get('type','') for p in state['players'] for c in p['battlefield'])
                if creatures>board_peaks[segment]['creatures']:
                    board_peaks[segment]={'permanents':permanents,'creatures':creatures,'turn':turn}
                if openings[segment] is None:openings[segment]=[c['name'] for c in me.get('hand',[])]
                for card in me.get('hand',[]):hands[segment][card['name']]+=1
        expected_end=seed_to_segment[int(re.search(r'-(\d+)$',file.parent.name)[1])]
        assert segment==expected_end,(file,segment,expected_end)
        priority[file.parent.name+'/'+file.stem]=count
    for file in sorted((run/'audit').rglob('evaluation-seat-*.jsonl')):
        decisions=collections.Counter();count=0
        for line in file.open():decisions[json.loads(line)['decision']]+=1;count+=1
        evaluation[file.parent.name+'/'+file.stem]={'rows':count,'decisions':dict(decisions)}
    for i,g in enumerate(games):
        g['peak_observed_creature_board']=board_peaks[i]
        if include_private_hands:
            g['opening_hand']=openings[i];g['hand_snapshot_occurrences']=dict(hands[i])
    return {'games':games,'summary':summaries,'performance':json.loads((run/'performance.json').read_text()),'metadata':json.loads((run/'metadata.json').read_text()),'log_sha256':{log.name:hashlib.sha256(log.read_bytes()).hexdigest() for log in logs},'priority_counts':priority,'evaluation_counts':evaluation,'audit_bytes':sum(p.stat().st_size for p in (run/'audit').rglob('*.jsonl'))}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_directory',type=Path);p.add_argument('--include-private-hands',action='store_true',help='Include private hand observations for local analysis; omit for public reports');a=p.parse_args()
    result={name:summarize(a.run_directory/name,a.include_private_hands) for name in ['apex','layered']}
    (a.run_directory/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,deck in result.items():
        for g in deck['games']:print(name,g['seed'],g['winner'],g['engine_ms'],g['last_logged_turn'],g['commander_casts'])
