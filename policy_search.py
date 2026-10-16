#!/usr/bin/env python3
"""Explore bounded ninjutsu coefficients using common seeds and outcome feedback.

Experimental search only. No automatic policy promotion or claim of generally
optimal tactics. New source versions use a new output directory.
"""
import argparse
import json
from pathlib import Path
import random
import time
import adaptive_pilot as a
import dragonmind
from referee_games import inspect

BOUNDS={'damage':(4,20),'hitPercent':(25,200),'dragon':(0,180),'mana':(0,16),'replay':(0,16),'bodyDivisor':(4,16)}
BASE={'damage':10,'hitPercent':100,'dragon':90,'mana':6,'replay':4,'bodyDivisor':8}


def sample_vector(rng,parent=None):
    if parent is None:return {k:rng.randint(lo,hi) for k,(lo,hi) in BOUNDS.items()}
    return {k:max(lo,min(hi,parent[k]+rng.randint(-max(1,(hi-lo)//3),max(1,(hi-lo)//3)))) for k,(lo,hi) in BOUNDS.items()}


def parent_candidate(candidates,rng):
    eligible=[i for i,c in enumerate(candidates) if any(g.get('feedback') is not None for g in c['games'])]
    if not eligible:return None
    return max(eligible,key=lambda i:rng.betavariate(1+sum(g.get('feedback')==1 for g in candidates[i]['games']),1+sum(g.get('feedback')==0 for g in candidates[i]['games'])))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['engine','jar','output']:p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--seed',type=int,required=True);p.add_argument('--candidates',type=int,default=3);p.add_argument('--timeout',type=int,default=120)
    p.add_argument('--pairs',type=int,default=4,help='Matched seed/seat conditions per vector; groups of four cover all seats of one seed')
    args=p.parse_args()
    if min(args.candidates,args.timeout,args.pairs)<1:p.error('Positive candidates, pairs and timeout required')
    for key in ['engine','jar','output']:setattr(args,key,getattr(args,key).resolve())
    args.output.mkdir(parents=True,exist_ok=True)
    names=['GGS_Current','Jaymie_Ezio','Gabe_Food','Destyn_Turtles']
    signature={'jar_sha256':a.sha(args.jar),'source_sha256':a.sha(Path(__file__)),'seed':args.seed,'timeout':args.timeout,'pairs':args.pairs,'seed_layout':'seed+condition//4; rotation=condition%4',
               'deck_sha256':{n:a.sha(dragonmind.ROOT/'decks'/(n+'.dck')) for n in names}}
    protocol=args.output/'protocol.json'
    if protocol.exists() and json.loads(protocol.read_text())!=signature:p.error('Inputs changed; choose a new output')
    a.atomic_json(protocol,signature)
    path=args.output/'search-state.json';state=json.loads(path.read_text()) if path.exists() else {'candidates':[],'promotion':'none; strategic review and held-out validation required','scope':'Six coefficients in a bounded ninjutsu heuristic, not full tactical learning'}
    for idx in range(args.candidates):
        if idx>=len(state['candidates']):
            rng=random.Random(args.seed+10000+idx);parent=parent_candidate(state['candidates'],rng) if idx>1 else None
            vector=BASE.copy() if idx==0 else sample_vector(rng,state['candidates'][parent]['weights'] if parent is not None else None)
            state['candidates'].append({'weights':vector,'parent_candidate':parent,'games':[]});a.atomic_json(path,state)
        candidate=state['candidates'][idx]
        for pair in range(len(candidate['games']),args.pairs):
            seed=args.seed+pair//4;rotation=pair%4;out=args.output/f'candidate-{idx:03d}'/f'pair-{pair}'
            if out.exists() and not (out/'attempt.json').exists():out.rename(out.with_name(out.name+'-interrupted-'+str(time.time_ns())))
            out.mkdir(parents=True,exist_ok=True)
            print(f'candidate {idx}, seed {seed}',flush=True)
            if (out/'attempt.json').exists():row=json.loads((out/'attempt.json').read_text())
            else:
                flags=['-Ddragonmind.strategyProfile=BALANCED','-Ddragonmind.boundedCombatForecast=true']+[f'-Ddragonmind.weight.{k}={v}' for k,v in candidate['weights'].items()]
                row=dragonmind.batch(args.engine,args.jar,out,'GGS_Current',rotation,[seed],args.timeout,True,True,extra_jvm_flags=tuple(flags))[0];a.atomic_json(out/'attempt.json',row)
            if a.sha(args.jar)!=signature['jar_sha256'] or any(a.sha(dragonmind.ROOT/'decks'/(n+'.dck'))!=h for n,h in signature['deck_sha256'].items()):raise ValueError('Experiment inputs changed')
            reports=inspect(out);row['integrity_report']=reports
            row['won']=row['status']=='completed' and row.get('winner')==f"Ai({row['seats'].index('GGS_Current')+1})-GGS_Current"
            row['feedback']=float(row['won']) if row['status']=='completed' and reports and all(r['record_integrity_passed'] for r in reports) else None
            candidate['games'].append(row);a.atomic_json(path,state);print(row['status'],row['feedback'],flush=True)
    print('Completed experimental batch; no policy promoted.',flush=True)


if __name__=='__main__':main()
