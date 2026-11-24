"""Independent verifier for the instrumented four-seat, sequential-setup opening format."""
from collections import Counter
from prospective_opening_audit import JavaRandom, bounded, permutation, snapshot_objects


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_opening(rows, seed):
    rng = JavaRandom(seed)
    draws = []
    frames = []
    game_id = rows[0]['evidence_game_id'] if rows else None
    require(isinstance(game_id,str) and game_id.startswith(str(seed)+':'), 'Wrong game seed binding')
    for index, row in enumerate(rows, 1):
        require(row['stream_sequence'] == index and row['evidence_game_id'] == game_id
                and row['rules_approved'] is False, 'Inconsistent opening stream')
        if row['kind'] == 'opening_random_bits':
            width = row['bits']
            require(rng.bits(width) == row['value'], 'Seeded randomness mismatch')
            draws.append((width,row['value']))
        else:
            frames.append(row)
        require(row['random_index'] == len(draws), 'Missing or reordered RNG receipt')
    frames = iter(frames)
    identities = {}
    seen_calls = set()
    last_rng = 0

    def frame(kind, hook=None, call=None, seat=None, initializing=None):
        r = next(frames, None)
        require(r is not None and r['kind'] == kind and (hook is None or r['hook'] == hook)
                and (call is None or r['call_id'] == call)
                and (seat is None or r['player_id'] == seat), 'Unexpected opening event or actor')
        if kind == 'opening_call':
            require(r['call_id'] not in seen_calls, 'Reused native call ID')
            seen_calls.add(r['call_id'])
        if 'state' in r:
            ps = r['state']['players']
            require([p['id'] for p in ps] == list(range(4)) and all(p['life']==40 for p in ps),
                    'Unexpected house seats or life')
            observed = snapshot_objects(r['state'])
            if initializing is not None:
                new = {k:v for k,v in observed.items() if k not in identities}
                require(all(v[1]==initializing for v in new.values()), 'Unexpected initialization owner')
                p = ps[initializing]
                require(not p['Hand'] and len(p['Library']) +
                        sum(c['commander'] for c in p['Command']) == 100,
                        'Opening deck or commander count')
                identities.update(new)
            require(identities == observed, 'Opening object identity changed')
        return r

    orders = {}
    shuffles = 0
    def ids(row,seat,zone):
        return [c['id'] for c in row['state']['players'][seat][zone]]

    def shuffle(seat, initial):
        nonlocal last_rng, shuffles
        before = frame('opening_call','shuffle',seat=seat,initializing=seat if initial else None)
        order = ids(before,seat,'Library')
        require(before['random_index']==last_rng and not ids(before,seat,'Hand'), 'Shuffle input state')
        if not initial:
            require(Counter(order)==Counter(orders[seat]), 'Redraw lost or gained cards')
        gen = frame('shuffle_generated',seat=seat)
        end = frame('opening_return','shuffle',call=before['call_id'])
        require(end['random_index']==gen['random_index'], 'RNG after generation')
        expected = permutation(order,draws[last_rng:gen['random_index']])
        require(gen['order']==expected==ids(end,seat,'Library'), 'Generated or installed shuffle mismatch')
        last_rng=gen['random_index']
        shuffles+=1
        orders[seat]=expected

    for seat in range(4):
        shuffle(seat,True)
    start_call=frame('opening_call','starting_player_selection')
    require(start_call['random_index']==last_rng,'Extra setup randomness')
    chooser=frame('opening_call','starting_player_choice')
    start=bounded(iter(draws[last_rng:chooser['random_index']]),4)
    require(chooser['random_index']==last_rng+1 and chooser['player_id']==start,'Starting chooser RNG')
    last_rng+=1
    for name, call in [('starting_player_choice',chooser),('starting_player_selection',start_call)]:
        ret=frame('opening_return',name,call=call['call_id'])
        require(ret['result']==start and ret['random_index']==last_rng,'Starting selection')
    def verify_hands(row):
        for seat, order in orders.items():
            require(Counter(ids(row,seat,'Hand'))==Counter(order[:7])
                    and ids(row,seat,'Library')==order[7:], 'Derived seven or library mismatch')
        require(row['random_index']==last_rng,'Unexpected randomness during declaration')

    group=frame('opening_call','mulligans')
    require(group['first_player_id']==start,'Starting seat mismatch')
    verify_hands(group)
    actors=[(start+i)%4 for i in range(4)]
    declarations=[]
    for revision in range(3):
        redraw=[]
        for seat in actors:
            entry=frame('opening_call','mulligan_decision',seat=seat)
            verify_hands(entry)
            ret=frame('opening_return','mulligan_decision',call=entry['call_id'])
            verify_hands(ret)
            require(type(ret['result']) is bool,'Invalid declaration')
            declarations.append(dict(game='opening',revision=revision,actor=str(seat),
                                     token='keep' if ret['result'] else 'redraw'))
            if not ret['result']:
                redraw.append(seat)
        for seat in redraw:
            shuffle(seat,False)
        if not redraw:
            break
        actors=redraw
    end=frame('opening_return','mulligans',call=group['call_id'])
    verify_hands(end)
    require(next(frames,None) is None and last_rng==len(draws),'Unexpected trailing opening event')
    return dict(declarations=declarations,seeded_rng_requests=len(draws),verified_shuffles=shuffles,
                final_seven_card_hands=4,first_player=start)
