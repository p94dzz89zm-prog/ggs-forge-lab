#!/usr/bin/env python3
"""Build a self-contained replay from the guided seat's recorded information only."""
import argparse,json,os,copy,re
from pathlib import Path

def verified_final_frame(frames, log):
    """Only display an outcome corroborated by an unambiguous completed game."""
    if not frames or re.search(r'Stopping slow match as draw|(?:(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*(?:Exception|Error)\b|Exception in thread|StackOverflowError|OutOfMemoryError)', log):
        return None
    winners=re.findall(r'^Game Outcome: (.+?) has won because (.+)$',log,re.M)
    results=re.findall(r'^Game Result: Game \d+ ended in \d+ ms\. (.+?) has won!',log,re.M)
    players=set(re.findall(r'^Game Outcome: (.+?) has (?:won|lost)\b',log,re.M))
    if len(winners)!=1 or len(results)!=1 or winners[0][0]!=results[0] or len(players)!=4:
        return None
    final=copy.deepcopy(frames[-1])
    final.update(outcome=winners[0][0]+' wins · '+winners[0][1],action='',
                 reason='Verified game result. Board shown is the last recorded state; final damage and token totals are not inferred.',stack=[])
    return final

def build(game_dir,card_dir,output,inline=None):
    decisions={d['request_id']:d for d in map(json.loads,(game_dir/'decisions.jsonl').read_text().splitlines())}
    frames=[];previous=None;seen_names=set()
    for row in map(json.loads,(game_dir/'bridge/transcript.jsonl').read_text().splitlines()):
        q=row['request'];s=q['state'];d=decisions.get(q['request_id'],{});players=[]
        for p in s['players']:
            cards=[dict(id=c['id'],n=c.get('name',''),t=c.get('type',''),cost=c.get('mana_cost',''),p=c.get('power',0),h=c.get('toughness',0),tap=c.get('tapped',False)) for c in p['battlefield']]
            seen_names.update(c['n'] for c in cards if c['n'])
            players.append(dict(id=p['id'],life=p['life'],handCount=p['hand_count'],cards=cards,hand=[c['name'] for c in p.get('hand',[])],grave=[c['name'] for c in p['graveyard']]))
        signature=json.dumps(players,sort_keys=True)
        mechanical=d.get('reason','').startswith(('Mechanical','Standing','External plan','External turn plan'))
        if signature==previous and q['kind']=='priority' and row.get('response',{}).get('index',-1)<0:continue
        if signature==previous and mechanical:continue
        previous=signature
        if mechanical and q['kind']=='priority' and s['stack']:continue
        response=row.get('response',{});action=''
        if q['kind']=='priority' and response.get('index',-1)>=0:
            action=q['options'][response['index']].get('description','')
        elif q['kind'] in ('entity','targets','cards'):
            indices=response.get('indices',[response['index']] if 'index' in response else [])
            action=' · '.join(q['options'][i].get('name','Choice') for i in indices if i>=0)
        elif q['kind'] in ('attack','block'):
            cards_by_id={c['id']:c.get('name','Manifest') for p in s['players'] for c in p['battlefield']}
            names={p['id']:p['name'].split('-',1)[-1] for p in s['players']}
            action=' · '.join(cards_by_id.get(int(pair.split(':')[0]),pair)+' → '+(names.get(int(pair.split(':')[1]),'') if q['kind']=='attack' else cards_by_id.get(int(pair.split(':')[1]),'')) for pair in response.get('pairs',[]))
        frames.append(dict(turn=s['turn'],active=s.get('active_player_id',0),phase=s['phase'],players=players,stack=[x.get('description',x.get('name','')) for x in s['stack']],reason=d.get('reason','Recorded state'),action=action))
    log=(game_dir/'game.log').read_text()
    final = verified_final_frame(frames, log)
    if final is not None:
        frames.append(final)
    oracle={}
    for folder,_,files in os.walk(card_dir,followlinks=True):
        for name in files:
            if not name.endswith('.txt'):continue
            content=(Path(folder)/name).read_text(errors='replace')
            lines=content.splitlines();card_name=next((l[5:] for l in lines if l.startswith('Name:')),None)
            if card_name in seen_names:
                oracle[card_name]=next((l[7:].replace('\\n',' ') for l in lines if l.startswith('Oracle:')),'')
    data=dict(frames=frames,oracle=oracle)
    encoded=json.dumps(data,separators=(',',':')).replace('</','<\\/')
    fragment=Path(__file__).with_name('replay-template.html').read_text().replace('__REPLAY_DATA__',encoded)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GGS pod replay</title></head><body>'+fragment+'</body></html>')
    if inline:inline.write_text(fragment)
    print(json.dumps({'frames':len(frames),'bytes':len(fragment.encode()),'output':str(output)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('game_dir',type=Path);p.add_argument('card_dir',type=Path);p.add_argument('output',type=Path);p.add_argument('--inline',type=Path);a=p.parse_args();build(a.game_dir,a.card_dir,a.output,a.inline)
