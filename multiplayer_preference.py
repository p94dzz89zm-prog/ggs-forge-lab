"""Experimental survival-contrast fit, never full-game reward admission.

Labels compare actual survival under a recorded single legal attack. They are
not calibrated game-winning probabilities or independent expert strategy.
"""
import argparse, hashlib, json, math
from pathlib import Path
from tactical_preference import probability

SCOPE='four_player_visible_survival_v1'
FEATURES=['bias','public_lethal_exposure_delta']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def audit_pair(row,power):
    """Separate arithmetic/resource referee, independent of feature prediction."""
    outcomes=[row['counter_outcome'],row['pass_outcome']]
    for o,counter in zip(outcomes,[True,False]):
        if (o['countered'] is not counter or o['targetSurvives'] is not counter
            or o['swanRetained'] is not (not counter) or o['blueUntapped'] is not (not counter)
            or o['birds']!=int(counter) or type(o['attackLegal']) is not bool
            or o['life']!=row['life']-power*int(o['attackLegal'])
            or o['survives'] is not (o['life']>0)):
            raise ValueError('Actual branch disagrees with arithmetic/resource referee')
    c,p=outcomes
    if c['survives']==p['survives']:raise ValueError('No verified survival contrast; abstain')
    if row['features']!=[1,int(p['attackLegal'])-int(c['attackLegal'])]:
        raise ValueError('Public forecast disagrees with actual attack branches')
    return int(c['survives'])

def load_reviewed(root):
    root=Path(root);review=json.loads((root/'review.json').read_text());data=root/'decisions.jsonl';log=root/'engine.log'
    if (review.get('scope')!=SCOPE or review.get('purpose')!='development'
        or review.get('data_sha256')!=sha(data) or review.get('engine_log_sha256')!=sha(log)
        or not review.get('reviewer') or not review.get('findings')
        or review.get('unresolved_in_scope')!=[] or review.get('full_game_admission') is not False):
        raise ValueError('Missing exact scoped development review')
    lines=log.read_text().splitlines();marker=review.get('completion_marker')
    if not marker or [x for x in lines if x.startswith('Checks passed:')]!=[marker] or any('AssertionError' in x or 'REGRESSION_LAUNCH_FAILURE' in x for x in lines):raise ValueError('Incomplete engine evidence')
    rows=[json.loads(x) for x in data.read_text().splitlines() if x.strip()]
    proof=[json.loads(x.split(' ',1)[1]) for x in lines if x.startswith('MULTIPLAYER_DATA ')]
    ids=[r['id'] for r in rows]
    if not rows or rows!=proof or len(ids)!=len(set(ids)) or set(ids)!=set(review.get('accepted_ids',[])) or set(ids)!=set(review.get('labels',{})):raise ValueError('Exact unique engine rows required')
    for r in rows:
        if (r.get('purpose')!='development' or r.get('scope')!=SCOPE or r.get('legal_paid_resolved') is not True
            or len(r.get('features',[]))!=2 or not all(type(x) in (int,float) and math.isfinite(x) for x in r['features'])):raise ValueError('Invalid development row')
        power=review.get('independent_body_power',{}).get(r['body'])
        if type(power) is not int or power<=0 or audit_pair(r,power)!=review['labels'][r['id']]:raise ValueError('Review label or independent rules input disagrees')
    return rows,review

def train(root,output):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve immutable candidate')
    rows,review=load_reviewed(root);weights=[0.0,0.0]
    for _ in range(600):
        gradient=[0.0,0.0]
        for r in rows:
            error=probability(weights,r['features'])-review['labels'][r['id']]
            for j,x in enumerate(r['features']):gradient[j]+=error*x/len(rows)
        weights=[w-.15*g for w,g in zip(weights,gradient)]
    model={'format':1,'scope':SCOPE,'features':FEATURES,'weights':weights,'baseline_weights':[0.0,0.0],
           'training_data_sha256':sha(Path(root)/'decisions.jsonl'),'review_sha256':sha(Path(root)/'review.json'),
           'training_ids':[r['id'] for r in rows],'training_examples':len(rows),'gradient_steps':600,'learning_rate':.15,
           'promotion':False,'full_game_admissions':0,'objective':'conditional survival under one recorded visible legal attack',
           'limitations':['Two constructed role templates, not independent expert multiplayer strategy','No calibrated probability of winning or full-game improvement']}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(model,f,indent=2);f.write('\n')
    return model
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(train(a.evidence,a.output),indent=2))
