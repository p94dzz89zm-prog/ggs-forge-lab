"""Verify a bounded decision-driven prefix; never a full-state/rules certificate."""
import argparse,json
from pathlib import Path
from decision_tape import choice
from executable_delta import digest

def initial(path):
    for line in Path(path).open():
        row=json.loads(line)
        if 'initial_state' in row:return row['initial_state']
    raise ValueError('Initial state absent')

def compatible(expected,actual):
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or not set(expected)<=set(actual):raise ValueError('Initial state fields missing')
        extra=set(actual)-set(expected)
        if extra-{'cast_ability_id','cast_chosen_x','cast_x_basis'}:raise ValueError('Unreviewed initial state addition')
        if any(actual[key] is not None for key in extra-{'cast_x_basis'}):raise ValueError('Non-null unbound cast history')
        for key,value in expected.items():compatible(value,actual[key])
    elif isinstance(expected,list):
        if not isinstance(actual,list) or len(expected)!=len(actual):raise ValueError('Initial state domain changed')
        for a,b in zip(expected,actual):compatible(a,b)
    elif expected!=actual:raise ValueError('Initial state value differs')

def verify(original,original_hash,decisions,replay,diagnostic,original_log,replay_log):
    if digest(original)!=original_hash:raise ValueError('Original hash mismatch')
    compatible(initial(original),initial(replay))
    failure=json.loads(Path(diagnostic).read_text());prefix=failure['decision_index']
    expected=[json.loads(line) for line in Path(decisions).open()]
    if expected[-1].get('kind')!='decision_tape_complete' or expected[-1].get('source_sha256')!=original_hash:raise ValueError('Unbound decision input')
    stack=[];completed=[]
    for line in Path(replay).open():
        row=json.loads(line)
        if row['kind']=='engine_call':
            controller=choice(row['hook']);root=controller and not any(item[1] for item in stack)
            stack.append((row,controller,root))
        elif row['kind']=='engine_return':
            if not stack or stack[-1][0]['call_id']!=row['call_id']:raise ValueError('Unpaired replay return')
            entry,_,root=stack.pop()
            if root:completed.append(entry)
    if len(completed)!=prefix:raise ValueError('Executed prefix differs from consumed decisions')
    for a,b in zip(expected[:prefix],completed):
        if a['kind']!='decision' or a['hook']!=b['hook'] or a['actor_id']!=b['receiver']['player_id']:raise ValueError('Choice order/actor differs')
        if any(b.get(key)!=value for key,value in a.get('context',{}).items()):raise ValueError('Choice context differs')
    transcript=Path(replay_log).read_text().split('DragonMind Result:')[0].rstrip()
    if not Path(original_log).read_text().startswith(transcript):raise ValueError('Canonical transcript prefix differs; review native identity text separately')
    return dict(supported_decisions=sum(row['kind']=='decision' for row in expected[:-1]),total_decisions=len(expected)-1,
                consecutive_completed_choices=prefix,engine_random_requests=failure['engine_random_requests_consumed'],
                canonical_prefix_lines=len(transcript.splitlines()),next_failure=failure['reason'],
                original_sha256=original_hash,decision_sha256=digest(decisions),replay_sha256=digest(replay),
                complete_state_reconstruction=False,complete_game=False,rules_approved=False,training_admission=False,
                scope='Initial state, completed controller calls/context and canonical transcript; independent legality still required')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('original','original_hash','decisions','replay','diagnostic','original_log','replay_log'):parser.add_argument('--'+name.replace('_','-'),required=True)
    print(json.dumps(verify(**vars(parser.parse_args())),indent=2))
