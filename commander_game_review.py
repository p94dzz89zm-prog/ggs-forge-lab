"""Replay-data checks and review leads, never a full-game rules certificate.

No score, review template or win can approve an episode here. Costs, priority,
replacement effects and strategic alternatives require substantive review.
"""
import argparse,hashlib,json
from pathlib import Path
from referee_games import inspect
from milestone_checkpoint import file_digest

def sha(path):return file_digest(path)
def audit_visibility(paths):
    viewers=set();snapshots=0;errors=[];leads=[];last_turn={};last_seen={};contexts=0
    for path in paths:
        try:
            with Path(path).open() as stream:
                for line_number,line in enumerate(stream,1):
                    row=json.loads(line);state=row.get('state',{});viewer=state.get('viewer_id')
                    if viewer is None:raise ValueError('Missing player-view state')
                    players=state.get('players');turn=state.get('turn')
                    if not isinstance(players,list) or type(turn) is not int or turn<0:raise ValueError('Missing players/turn')
                    own=[p for p in players if p.get('id')==viewer]
                    if len(own)!=1 or not isinstance(own[0].get('hand'),list):raise ValueError('Missing selected-seat hand')
                    if turn<last_turn.get(viewer,-1):raise ValueError('Turn index decreased within one viewer stream')
                    last_turn[viewer]=turn;viewers.add(state.get('viewer'));snapshots+=1
                    for player in players:
                        if any(k in player for k in ('library','library_order')):raise ValueError('Private library identities in player-view snapshot')
                        if player.get('id')!=viewer and 'hand' in player:raise ValueError('Opponent hand identities in player-view snapshot')
                        if turn>=last_seen.get(player.get('name'),{}).get('turn',-1):
                            last_seen[player.get('name')]={'turn':turn,'life':player.get('life')}
                    # Only a context prefilter: this is NOT proof the model fired
                    # or the counterspell was payable/stock-selected.
                    if (len(players)==4 and state.get('phase')=='MAIN1' and state.get('active_player_id')!=viewer
                            and any(c.get('name')=='Swan Song' for c in own[0]['hand'])
                            and len(state.get('stack',[]))==1):contexts+=1
        except (OSError,ValueError,TypeError,KeyError) as error:
            errors.append({'file':Path(path).name,'line':locals().get('line_number'),'issue':str(error)})
    if not paths:errors.append({'issue':'No all-seat audit streams'})
    return {'snapshots_checked':snapshots,'viewers':sorted(x for x in viewers if isinstance(x,str)),
            'visibility_or_record_errors':errors,'review_leads':leads,'last_observed_player_states':last_seen,
            'counter_context_prefilter_snapshots':contexts,'model_activation_count':None,
            'scope':'hand/library identity and viewer-stream integrity only; revealed-card and face-down semantics need separate review'}

def saved_evidence(root):
    """Bind a review to finalized hashes; truncated but valid JSON must fail."""
    root=Path(root).resolve();issues=[];checked=0
    try:
        state=json.loads((root.parent/'state.json').read_text())
        entries=[a for a in state['attempts'] if a.get('label')==root.name]
        if len(entries)!=1 or entries[0].get('status')!='saved' or not entries[0].get('complete'):
            raise ValueError('No unique finalized complete attempt for selected side')
        expected=entries[0].get('evidence_sha256')
        if not isinstance(expected,dict) or not expected:raise ValueError('Missing finalized evidence hashes')
        for relative,want in expected.items():
            path=root/relative
            if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError('Unsafe finalized evidence path')
            if not path.is_file():issues.append({'file':relative,'issue':'Finalized evidence missing'});continue
            actual=sha(path);checked+=1
            if actual!=want:issues.append({'file':relative,'issue':'Finalized evidence hash mismatch','expected_sha256':want,'actual_sha256':actual})
        actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.log','.partial') and 'runtime-home' not in p.parts}
        for extra in sorted(actual-set(expected)):issues.append({'file':extra,'issue':'Unbound evidence file'})
    except (OSError,ValueError,TypeError,KeyError) as error:
        issues.append({'issue':str(error)})
    return {'passed':not issues,'files_checked':checked,'issues':issues,
            'scope':'Finalized journal binding; no repair, rehash acceptance or full-game rules approval'}

def review(root):
    root=Path(root);binding=saved_evidence(root);reports=inspect(root);audit=audit_visibility(sorted((root/'audit').rglob('seat-*.jsonl')))
    attempt=json.loads((root/'attempt.json').read_text());seats=attempt.get('seats',[])
    registered={f'Ai({i+1})-{name}' for i,name in enumerate(seats)}
    issues=list(binding['issues'])+list(audit['visibility_or_record_errors'])
    if set(audit['viewers'])!=registered:issues.append({'issue':'Missing/extra registered-seat audit coverage'})
    if len(reports)!=1 or not all(r['record_integrity_passed'] for r in reports):issues.append({'issue':'Canonical record integrity failed'})
    return {'scope':'full-game evidence preflight, not full-game approval','record_and_visibility_preflight_passed':not issues,
            'issues':issues,'saved_evidence':binding,'audit':audit,'canonical_reports':reports,'seed':attempt.get('seed'),
            'recorded_status':attempt.get('status'),'recorded_winner':attempt.get('winner'),
            'last_logged_turn':attempt.get('last_logged_turn'),'reviewed_rules_valid_games':0,
            'strategic_review':'pending','learning_admission':False,
            'unverified_mechanics':['priority and response alternatives','actual costs and targets for every action',
                'combat/blocking/lethal correctness','trigger/replacement resolution','commander tax/damage/zone choices',
                'multiplayer elimination order and cleanup','GGS/ninjutsu/extra-combat decision quality'],
            'limitations':['A complete canonical result is not proof of rules-correct or strategically sound play.',
                'Last observed life/turn is not exact elimination timing or survival duration.',
                'Context-prefilter counts are not observed model activation or verified missed opportunities.']}

def trajectory_digest(transcript):
    """Compare recorded gameplay events, excluding only explicit timing/result metadata."""
    lines=Path(transcript).read_text().splitlines()
    events=[line for line in lines if not line.startswith(('DragonMind Result: ','Game Outcome: Match Duration '))]
    return hashlib.sha256(('\n'.join(events)+'\n').encode()).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=review(a.root);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'preflight':result['record_and_visibility_preflight_passed'],'reviewed_rules_valid_games':0,'snapshots':result['audit']['snapshots_checked']}))
    raise SystemExit(0 if result['record_and_visibility_preflight_passed'] else 1)
