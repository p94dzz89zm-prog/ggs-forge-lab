#!/usr/bin/env python3
"""Query the complete pinned Oracle index and retain noncausal weakness observations.

Rules text and engine definition coverage are not simulated performance. Every
search result retains that boundary. Stored game observations remain separated
by deck variant; none is automatically a card-cut verdict.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
from referee_games import inspect


def connection(path):
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)


def search(path, query, roles=(), limit=20):
    db=connection(path);db.row_factory=sqlite3.Row
    where=['c.grixis_eligible=1'];params=[]
    if query:
        where.append('c.oracle_id IN (SELECT oracle_id FROM search WHERE search MATCH ?)');params.append(query)
    if roles:
        where.append('c.oracle_id IN (SELECT oracle_id FROM role_matches WHERE role IN ('+','.join('?' for _ in roles)+'))');params.extend(roles)
    rows=db.execute('SELECT c.* FROM cards c WHERE '+' AND '.join(where)+' ORDER BY c.in_deck DESC,c.mana_value,c.name LIMIT ?',(*params,limit)).fetchall()
    results=[]
    for row in rows:
        item=dict(row)
        item['role_evidence']=[{'role':r,'matched_text':e} for r,e in db.execute('SELECT role,matched_text FROM role_matches WHERE oracle_id=?',(row['oracle_id'],))]
        results.append(item)
    db.close();return results


def observations(path):
    turns={};seen=set();held=set()
    with path.open() as stream:
        for line in stream:
            row=json.loads(line);state=row.get('state',{})
            if row.get('kind')!='priority' or state.get('active_player_id')!=state.get('viewer_id'):continue
            own=next(p for p in state['players'] if p['id']==state['viewer_id'])
            held={c['name'] for c in own.get('hand',[])};seen.update(held)
            if state.get('phase')!='MAIN1':continue
            board=own['battlefield']
            turns.setdefault(state['turn'],{'turn':state['turn'],'life':own['life'],'hand':own['hand_count'],
              'lands':sum('Land' in c.get('type','') for c in board),
              'creatures':sum('Creature' in c.get('type','') for c in board),
              'ggs':any(c['name']=='Goro-Goro and Satoru' for c in board)})
    return list(turns.values()),seen,held


def engine_provenance(record):
    for parent in record.parents:
        for name in ['manifest.json','protocol.json','cycle-protocol.json']:
            path=parent/name
            if not path.is_file():continue
            try:metadata=json.loads(path.read_text())
            except (ValueError,OSError):continue
            value=metadata.get('jar_sha256') or metadata.get('engine_sha256')
            if value:return value
    return 'unknown'


def watch(directories, output):
    output.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(output/'weakness-watch.sqlite')
    db.executescript('''CREATE TABLE IF NOT EXISTS games(transcript_sha256 TEXT PRIMARY KEY,record_path TEXT,status TEXT,variant TEXT);
      CREATE TABLE IF NOT EXISTS turns(transcript_sha256 TEXT,global_turn INTEGER,own_turn INTEGER,life INTEGER,hand_count INTEGER,lands INTEGER,creatures INTEGER,ggs_present INTEGER,PRIMARY KEY(transcript_sha256,global_turn));
      CREATE TABLE IF NOT EXISTS card_exposure(transcript_sha256 TEXT,name TEXT,seen_in_hand INTEGER,last_snapshot_in_hand INTEGER,PRIMARY KEY(transcript_sha256,name));''')
    if 'engine_sha256' not in {r[1] for r in db.execute('PRAGMA table_info(games)')}:
        db.execute('ALTER TABLE games ADD COLUMN engine_sha256 TEXT')
        for digest,path in db.execute('SELECT transcript_sha256,record_path FROM games').fetchall():
            db.execute('UPDATE games SET engine_sha256=? WHERE transcript_sha256=?',(engine_provenance(Path(path)),digest))
        db.commit()
    for root in directories:
        for report in inspect(root):
            if not report['record_integrity_passed']:continue
            digest=report['transcript_sha256']
            if db.execute('SELECT 1 FROM games WHERE transcript_sha256=?',(digest,)).fetchone():continue
            record=Path(report['record']);label=record.parent.name
            audits=list((record.parents[2]/'audit'/label).glob('seat-*.jsonl'))
            variant=label.split('__seat')[0]
            selected=[]
            for path in audits:
                with path.open() as stream:
                    first=next((json.loads(line) for line in stream if line.strip()),{})
                if first.get('state',{}).get('viewer','').endswith('-'+variant):selected.append(path)
            if len(selected)!=1:continue
            turns,seen,held=observations(selected[0])
            db.execute('INSERT INTO games VALUES(?,?,?,?,?)',(digest,str(record),report['status'],label.split('__seat')[0],engine_provenance(record)))
            db.executemany('INSERT INTO turns VALUES(?,?,?,?,?,?,?,?)',[(digest,t['turn'],i,t['life'],t['hand'],t['lands'],t['creatures'],t['ggs']) for i,t in enumerate(turns,1)])
            db.executemany('INSERT INTO card_exposure VALUES(?,?,?,?)',[(digest,n,1,n in held) for n in seen]);db.commit()
    columns=['engine_sha256','variant','snapshots_from_personal_turn4','empty_hand','no_creatures','two_or_fewer_lands','ggs_absent']
    grouped=[dict(zip(columns,r)) for r in db.execute('SELECT g.engine_sha256,g.variant,COUNT(*),SUM(t.hand_count=0),SUM(t.creatures=0),SUM(t.lands<=2),SUM(t.ggs_present=0) FROM turns t JOIN games g USING(transcript_sha256) WHERE own_turn>=4 GROUP BY g.engine_sha256,g.variant')]
    data={'integrity_passed_games_with_selected_seat_audits':db.execute('SELECT COUNT(*) FROM games').fetchone()[0],
      'by_deck_variant':grouped,'causal_card_cut_recommendations':[],
      'trusted_card_recommendation_games':0,'observation_review_status':'unreviewed noncausal diagnostics; not admitted learning evidence',
      'limits':'First MAIN1 snapshots, not end-turn failures. No creatures can follow a wipe, deployment choice, or draw pattern. A held card can be correct protection. Distinct deck variants and engine versions must not be interpreted as one controlled experiment.'}
    (output/'weakness-watch.json').write_text(json.dumps(data,indent=2)+'\n');db.close();return data


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    s=sub.add_parser('search');s.add_argument('--index',type=Path,required=True);s.add_argument('--query',default='');s.add_argument('--roles',nargs='*',default=[]);s.add_argument('--limit',type=int,default=20)
    w=sub.add_parser('watch');w.add_argument('--runs',nargs='+',type=Path,required=True);w.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='search':
        if not 1<=args.limit<=100:parser.error('Limit must be 1 to 100')
        result=search(args.index,args.query,args.roles,args.limit)
    else:result=watch(args.runs,args.output)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
