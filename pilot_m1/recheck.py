"""Reopen live opening evidence and inject one change at a time into private copies."""
from copy import deepcopy
import json
from pathlib import Path
from . import references
from .lesson import replay
from .native import file_hash, verify_trace
from .policy import encode


def recorded(run):
    paths=[p for p in (run/'opening.jsonl',run/'opening.jsonl.partial') if p.is_file()]
    if len(paths)!=1:
        raise ValueError('Expected one opening tape')
    with paths[0].open() as f:
        rows=[json.loads(line) for line in f]
    by_seat={}
    for directory in sorted((run/'workers').glob('pilot-*')):
        cfg=json.loads((directory/'config.json').read_text())
        journal=directory/'decisions.jsonl'
        receipt=json.loads((directory/'opening-receipt.json').read_text())
        if file_hash(journal)!=receipt['journal_sha256']:
            raise ValueError('Journal digest mismatch')
        with journal.open() as f:
            by_seat[cfg['seat']]=iter(list(replay(cfg,map(json.loads,f))))
    logs=[next(by_seat[r['player_id']]) for r in rows
          if r['kind']=='opening_call' and r['hook']=='mulligan_decision']
    if any(next(it,None) is not None for it in by_seat.values()):
        raise ValueError('Extra pilot decisions')
    return rows,logs


def check(run,seed,reference):
    rows,logs=recorded(run)
    choices=[r['selection'] for r in logs]
    offers=[r['offer'] for r in logs]
    def validate(tape,actions,views):
        receipt=verify_trace(tape,actions,seed)
        references.check(tape,views,reference)
        return receipt
    positive=validate(rows,choices,offers)
    cases={}
    def reject(name,tape,actions=choices,views=offers):
        try:
            validate(tape,actions,views)
        except (ValueError,KeyError) as e:
            cases[name]=str(e)
        else:
            raise AssertionError('Mutation survived: '+name)
    bad=deepcopy(rows)
    draw=next(r for r in bad if r['kind']=='opening_random_bits')
    draw['value']^=1
    reject('changed RNG value',bad)
    reject('missing RNG capture',[r for r in rows if r['kind']!='opening_random_bits'])
    bad=deepcopy(rows)
    gen=next(r for r in bad if r['kind']=='shuffle_generated')
    gen['order'][0],gen['order'][1]=gen['order'][1],gen['order'][0]
    reject('changed generated order',bad)
    bad=deepcopy(rows)
    calls=[r for r in bad if r['kind']=='opening_call' and r['hook']=='shuffle']
    calls[1]['state']['players'][0]['Library'][0]['name']='Changed object from prior seat'
    reject('earlier seat mutated during later initialization',bad)
    bad=deepcopy(rows)
    hand=bad[-1]['state']['players'][0]['Hand']
    library=bad[-1]['state']['players'][0]['Library']
    hand[0],library[0]=library[0],hand[0]
    reject('wrong final drawn card',bad)
    bad=deepcopy(choices)
    bad[0]['token']='redraw' if bad[0]['token']=='keep' else 'keep'
    reject('inverted native declaration',rows,bad)
    bad=deepcopy(choices)
    bad[0]['actor']=str((1+int(bad[0]['actor']))%4)
    reject('misrouted native declaration',rows,bad)
    bad=deepcopy(offers)
    bad[0]['observation']['cheap_commander']=not bad[0]['observation']['cheap_commander']
    reject('wrong actor-private feature',rows,choices,bad)
    return dict(positive=positive,verified_actor_views=len(offers),rejected=cases)


if __name__=='__main__':
    import sys
    run,seed,ref=sys.argv[1:]
    print(encode(check(Path(run),int(seed),json.loads(Path(ref).read_text()))))
