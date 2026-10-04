"""Allowlisted outcomes and seed-clustered differential analysis of matched pods."""
import argparse, collections, json, random, statistics
from pathlib import Path

VALID = {'completed', 'completed_draw'}
PUBLIC_GAME_FIELDS = ('seed', 'status', 'winner', 'engine_ms', 'last_logged_turn',
    'commander_casts', 'peak_observed_creature_board', 'peak_observed_ggs_creatures',
    'excluded_priority_snapshots_without_ggs', 'ggs_outcome_reason', 'observed_combat_turns')

def bootstrap_win_difference(pairs, iterations=10000):
    # All four seat rotations share a seed: resample whole seeds, not individual games.
    grouped = collections.defaultdict(list)
    for apex, layered in pairs:
        grouped[apex['seed']].append(int(apex['ggs_win'])-int(layered['ggs_win']))
    clusters = list(grouped.values())
    if not clusters:
        return None
    rng = random.Random(20261004); values = []
    for _ in range(iterations):
        sample = [rng.choice(clusters) for _ in clusters]
        values.append(sum(map(sum, sample))/sum(map(len, sample)))
    values.sort()
    return {'difference_apex_minus_layered': sum(map(sum, clusters))/sum(map(len, clusters)),
        'approximate_95_percentile_interval': [values[int(.025*iterations)], values[int(.975*iterations)]],
        'seed_clusters': len(clusters), 'iterations': iterations,
        'method': 'Paired percentile bootstrap resampling whole seed clusters; exploratory, conditional on valid pairs'}

def unresolved_outcome_bounds(all_valid, planned):
    bounds={}
    for name, result in all_valid.items():
        known_wins=result.get('wins',0); missing=planned-result['games']
        bounds[name]={'unresolved_slots':missing,
            'possible_scheduled_win_rate_range':[known_wins/planned,(known_wins+missing)/planned]}
    apex=bounds['apex']['possible_scheduled_win_rate_range']
    layered=bounds['layered']['possible_scheduled_win_rate_range']
    return {'by_deck':bounds,'possible_apex_minus_layered_scheduled_win_rate_range':
        [apex[0]-layered[1],apex[1]-layered[0]],
        'meaning':'Worst-case bounds for unknown outcomes, not estimates or confidence intervals; invalid games are not assigned wins or losses'}

def metrics(rows):
    first = [g['commander_casts'][0]['own_turn'] for g in rows
             if g['commander_casts'] and g['commander_casts'][0]['own_turn'] is not None]
    durations = sorted(g['engine_ms']/1000 for g in rows)
    combats = [c for g in rows for c in g['observed_combat_turns'].values()]
    if not rows:
        return {'games': 0}
    return {'games': len(rows), 'wins': sum(g['ggs_win'] for g in rows),
        'win_rate': sum(g['ggs_win'] for g in rows)/len(rows),
        'draws': sum(g['status']=='completed_draw' for g in rows),
        'wins_by_seat': {s: sum(g['ggs_win'] for g in rows if g['ggs_seat']==s) for s in range(4)},
        'games_by_seat': {s: sum(g['ggs_seat']==s for g in rows) for s in range(4)},
        'opponent_wins': dict(collections.Counter(g['winner'].split('-',1)[1]
                              for g in rows if g['winner'] and not g['ggs_win'])),
        'median_engine_seconds': statistics.median(durations),
        'p90_engine_seconds_nearest_rank': durations[max(0, (9*len(durations)+9)//10-1)],
        'median_first_commander_cast_own_turn': statistics.median(first) if first else None,
        'games_without_logged_commander_cast': sum(not g['commander_casts'] for g in rows),
        'commander_recast_events': sum(max(0,len(g['commander_casts'])-1) for g in rows),
        'logged_ggs_triggers': sum(g['logged_ggs_triggers'] for g in rows),
        'median_logged_ggs_triggers': statistics.median(g['logged_ggs_triggers'] for g in rows),
        'ninjutsu_paid_return_records': sum(g['ninjutsu_paid_return_records'] for g in rows),
        'median_peak_observed_ggs_creatures': statistics.median(g['peak_observed_ggs_creatures'] for g in rows),
        'observed_combat_turns_with_ggs': sum(c['ggs_named_creature_seen'] for c in combats),
        'fresh_attack_turns_with_ggs': sum(c['fresh_attack_with_ggs_seen'] for c in combats),
        'fresh_unblocked_turns_with_ggs': sum(c['fresh_unblocked_with_ggs_seen'] for c in combats),
        'median_global_finish_turn_on_wins': statistics.median(g['last_logged_turn'] for g in rows if g['ggs_win']) if any(g['ggs_win'] for g in rows) else None}

def analyze(root):
    selected = json.loads((root/'selected.json').read_text())
    protocol = json.loads((root/'protocol.json').read_text())
    assert len(selected)==2*protocol['planned_games_per_deck']
    assert len({(r['deck'],r['rotation'],r['seed']) for r in selected})==len(selected)
    public = {n: [] for n in ('apex','layered')}; hashes = {}; failures = []
    for slot in selected:
        if slot['status'] not in VALID:
            failures.append(slot); continue
        folder = root/slot['folder']; data = json.loads((folder/'analysis.json').read_text())
        assert len(data['games'])==1
        game = data['games'][0]; summary = data['summary'][0]
        assert game['seed']==slot['seed'] and summary['seat_rotation']==slot['rotation']
        assert data['metadata']['jar_sha256']==protocol['metadata'][slot['deck']]['jar_sha256']
        seat = summary['seats'].index(summary['variant'])
        row = {k:game[k] for k in PUBLIC_GAME_FIELDS}
        row.update(rotation=slot['rotation'],ggs_seat=seat,
            ggs_win=game['winner']==f'Ai({seat+1})-'+summary['variant'],
            logged_ggs_triggers=game['trigger_counts'].get('Goro-Goro and Satoru',0),
            ninjutsu_paid_return_records=game['ninjutsu_evaluation_counts'].get('paid_return',0))
        public[slot['deck']].append(row)
        hashes[slot['folder']] = data['log_sha256']
    indexed = {n:{(g['rotation'],g['seed']):g for g in rows} for n,rows in public.items()}
    common = indexed['apex'].keys() & indexed['layered'].keys()
    pairs = [(indexed['apex'][k],indexed['layered'][k]) for k in sorted(common)]
    for rows in public.values():
        rows.sort(key=lambda g:(g['seed'],g['rotation']))
        for g in rows:
            g['matched_valid_pair']=(g['rotation'],g['seed']) in common
    paired = {n:metrics([g for g in rows if g['matched_valid_pair']]) for n,rows in public.items()}
    comparison = {'planned_games_per_deck':protocol['planned_games_per_deck'],
        'matched_valid_pairs':len(pairs), 'all_valid':{n:metrics(rows) for n,rows in public.items()},
        'matched':paired, 'win_difference':bootstrap_win_difference(pairs),
        'paired_outcomes':dict(collections.Counter(
            'both_win' if a['ggs_win'] and b['ggs_win'] else 'apex_only_win' if a['ggs_win']
            else 'layered_only_win' if b['ggs_win'] else 'neither_win' for a,b in pairs)),
        'unresolved_slots':failures}
    comparison['unresolved_outcome_sensitivity']=unresolved_outcome_bounds(
        comparison['all_valid'],comparison['planned_games_per_deck'])
    return {'games':public,'metadata':protocol['metadata'],'log_sha256':hashes},comparison

def report(comparison):
    lines = ['# Apex versus Layered: 100 scheduled pod games per deck', '',
        f"Matched valid pairs: **{comparison['matched_valid_pairs']}**. Unresolved slots: **{len(comparison['unresolved_slots'])}**.", '',
        'Both decks faced Jaymie’s supplied Ezio list, the Food and Fellowship proxy, and the Turtle Power proxy—not each other in the same game. Decklists, v17 engine, AI policies and allowances stayed fixed.', '',
        'Twenty-five fresh seeds were rotated through all four seats. Game order was prespecified and shuffled, deck submission order alternated, and two independent JVM workers were used. Invalid slots received one identical-settings retry; unresolved slots are not wins or losses. The matched-valid subset is the primary comparison.', '',
        '| Matched metric | Apex | Layered |', '|---|---:|---:|']
    for label,key in [('Games','games'),('Wins','wins'),('Win rate','win_rate'),
        ('Median engine seconds','median_engine_seconds'),('90th-percentile engine seconds','p90_engine_seconds_nearest_rank'),
        ('Median first commander cast: own turn','median_first_commander_cast_own_turn'),
        ('Games without logged commander cast','games_without_logged_commander_cast'),
        ('Commander recast events','commander_recast_events'),('Logged GGS triggers','logged_ggs_triggers'),
        ('Ninjutsu paid-return records','ninjutsu_paid_return_records'),
        ('Median peak observed GGS creatures','median_peak_observed_ggs_creatures'),
        ('Fresh attack turns with GGS observed','fresh_attack_turns_with_ggs'),
        ('Fresh unblocked turns with GGS observed','fresh_unblocked_turns_with_ggs'),
        ('Median global finish turn on GGS wins','median_global_finish_turn_on_wins')]:
        values=[comparison['matched'][n].get(key) for n in ('apex','layered')]
        display=[f'{v:.1%}' if key=='win_rate' and v is not None else f'{v:.3f}' if isinstance(v,float) else str(v) for v in values]
        lines.append(f'| {label} | {display[0]} | {display[1]} |')
    estimate=comparison['win_difference']
    if estimate:
        low,high=estimate['approximate_95_percentile_interval']
        lines += ['', f"Apex-minus-Layered matched win-rate difference: **{100*estimate['difference_apex_minus_layered']:.1f} percentage points**. Exploratory seed-clustered bootstrap interval: **{100*low:.1f} to {100*high:.1f} points**.", '',
            'The bootstrap resamples entire seed clusters, preserving the dependence among their four seat rotations. It is approximate, small-sample and conditional on valid pairs; it is not a guarantee of human-pod superiority. An interval crossing zero does not establish a clear ranking.']
    sensitivity=comparison.get('unresolved_outcome_sensitivity')
    if sensitivity:
        low,high=sensitivity['possible_apex_minus_layered_scheduled_win_rate_range']
        lines += ['',f'If unresolved outcomes are allowed to range from all losses to all wins, the possible Apex-minus-Layered difference across all scheduled slots ranges from **{100*low:.1f} to {100*high:.1f} percentage points**. These are worst-case unknown-outcome bounds—not estimates or confidence intervals—and no invalid game is assigned a result.']
    lines += ['', '## Interpretation limits', '',
        'Wins are the primary endpoint. Secondary metrics describe activity and possible mechanisms, not causal card value. Announced GGS triggers are not verified resolved Dragon tokens; paid-return records are not independent opportunities; combat metrics union observations within a turn and may include extra combats. Face-down identities and post-elimination viewer gaps limit board observations. First-cast medians exclude games without a logged cast, whose counts are reported separately.', '',
        'Audits and concurrent workers affect duration. These are descriptive collection times, not a controlled speed benchmark. Shared initial seeds do not force identical subsequent random choices once deck-dependent play diverges. Proxy opponents and AI piloting limit transfer to actual games. Unresolved games may be non-random, so failure counts and all-valid results accompany the matched analysis.', '',
        'Raw logs, all attempts and private audits are retained in the saved data archive. Public exports use explicit numeric/outcome allowlists and exclude hands, raw AI decision strings and card-level action records.', '']
    return '\n'.join(lines)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    public,comparison=analyze(args.root);args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'analysis.json').write_text(json.dumps(public,indent=2)+'\n')
    (args.output/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    (args.output/'GGS_100_Game_Comparison.md').write_text(report(comparison))
    print(json.dumps(comparison,indent=2))
