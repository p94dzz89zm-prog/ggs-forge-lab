#!/usr/bin/env python3
"""Experimental supervised decision preferences, separate from full-game rewards.

Only explicitly reviewed, engine-executed decision pairs may train. This narrow
local preference model cannot admit an episode or establish a win-rate gain.
"""
import argparse, hashlib, json, math
from pathlib import Path
FEATURES=['bias','own_target','target_power_scaled','life_scaled']
SCOPE='scoped_counterspell_preference_v1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def probability(weights, features):
    z=sum(w*x for w,x in zip(weights,features))
    return 1/(1+math.exp(-max(-40,min(40,z))))
def load_reviewed(root):
    root=Path(root);review=json.loads((root/'review.json').read_text());data=root/'decisions.jsonl';proof=root/'engine.log'
    if review.get('scope')!=SCOPE or review.get('purpose')!='development' or review.get('data_sha256')!=sha(data) or review.get('engine_log_sha256')!=sha(proof):raise ValueError('Missing exact scoped development evidence')
    if not review.get('reviewer') or not review.get('findings') or review.get('unresolved_in_scope')!=[]:raise ValueError('Substantive scoped review required')
    lines=proof.read_text().splitlines();marker=review.get('completion_marker')
    if not marker or [x for x in lines if x.startswith('Checks passed:')]!=[marker] or any('AssertionError' in x or 'Exception in thread' in x for x in lines):raise ValueError('Engine evidence incomplete')
    rows=[json.loads(x) for x in data.read_text().splitlines() if x.strip()]
    ids=[x['id'] for x in rows]
    if not rows or len(ids)!=len(set(ids)) or set(ids)!=set(review.get('accepted_ids',[])):raise ValueError('Exact unique decision allocation required')
    proof_rows={json.loads(x[len('TACTICAL_DATA '):])['id']:json.loads(x[len('TACTICAL_DATA '):]) for x in lines if x.startswith('TACTICAL_DATA ')}
    if set(review.get('labels',{}))!=set(ids):raise ValueError('Every label requires explicit review')
    for r in rows:
        if proof_rows.get(r['id'])!=r:raise ValueError('Decision differs from actual engine output')
        r['label_counter']=review['labels'][r['id']]
        if r.get('purpose')!='development' or r.get('scope')!=SCOPE or r.get('legal_paid_resolved') is not True or r.get('label_counter') not in (0,1):raise ValueError('Invalid decision evidence')
        if len(r['features'])!=len(FEATURES) or not all(isinstance(x,(float,int)) and math.isfinite(x) for x in r['features']):raise ValueError('Invalid features')
        if not r.get('counter_outcome') or not r.get('pass_outcome'):raise ValueError('Both actual branches required')
    return rows,review

def train(root,output,steps=600,rate=.15):
    out=Path(output)
    if out.exists():raise FileExistsError('Frozen model must not be overwritten')
    rows,review=load_reviewed(root);weights=[0.0]*len(FEATURES)
    baseline=[probability(weights,r['features']) for r in rows]
    for _ in range(steps):
        gradient=[0.0]*len(weights)
        for r in rows:
            error=probability(weights,r['features'])-r['label_counter']
            for j,x in enumerate(r['features']):gradient[j]+=error*x/len(rows)
        weights=[w-rate*g for w,g in zip(weights,gradient)]
    model={'format':1,'scope':SCOPE,'features':FEATURES,'weights':weights,'baseline_weights':[0.0]*len(FEATURES),
           'training_data_sha256':sha(Path(root)/'decisions.jsonl'),'review_sha256':sha(Path(root)/'review.json'),
           'training_ids':[r['id'] for r in rows],'training_examples':len(rows),'gradient_steps':steps,'learning_rate':rate,
           'training_probabilities_before':baseline,'training_probabilities_after':[probability(weights,r['features']) for r in rows],
           'promotion':False,'full_game_admissions':0,'limitations':['Local reviewed preference only; no general strategic or win-rate improvement established','No hidden-state inference or complete-game reward feedback']}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(model,f,indent=2);f.write('\n')
    return model
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(train(a.evidence,a.output),indent=2))
