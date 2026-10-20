"""Compare two jars on disjoint new seed groups, reversing jar order by group."""
from trace_compare import read_games, compare
from pathlib import Path
import argparse, hashlib, json, re, subprocess

parser = argparse.ArgumentParser(description=__doc__)
for name in ['control_jar', 'candidate_jar', 'deck_directory', 'resource_directory', 'output_directory']:
    parser.add_argument(name, type=Path)
parser.add_argument('--seeds', nargs='+', type=int, default=list(range(20261013, 20261019)))
parser.add_argument("--resume", action="store_true", help="Read existing run logs; run missing groups only")
args = parser.parse_args()
if len(args.seeds) < 2 or len(set(args.seeds)) != len(args.seeds):
    parser.error('Supply at least two distinct seeds')
root = args.output_directory.resolve()
root.mkdir(parents=True, exist_ok=True)
categories = {'Turn', 'Phase', 'Add To Stack', 'Resolve Stack', 'Damage', 'Combat', 'Life'}
midpoint = (len(args.seeds) + 1) // 2
groups = [args.seeds[:midpoint], args.seeds[midpoint:]]
results = {'seeds': args.seeds, 'jar_sha256': {
    label: hashlib.sha256(jar.read_bytes()).hexdigest()
    for label, jar in [('control', args.control_jar), ('candidate', args.candidate_jar)]},
    'runs': {}, 'comparisons': []}
traces = {}
for group_index, seeds in enumerate(groups):
    order = [('control', args.control_jar), ('candidate', args.candidate_jar)]
    if group_index % 2:
        order.reverse()
    for label, jar in order:
        run = f'group-{group_index + 1}-{label}'
        print('Starting ' + run + ': ' + str(seeds), flush=True)
        command = ['java', '-Xmx1536m', '-XX:+UseParallelGC', '-XX:-TieredCompilation',
                   '-XX:CompileThreshold=1000', '-XX:-UsePerfData', '-Djava.awt.headless=true',
                   '-cp', str(jar.resolve()), 'forge.view.Main', 'sim', '-D',
                   str(args.deck_directory.resolve()), '-d', 'GGS_Layered_v1.dck',
                   'Jaymie_Ezio.dck', 'Gabe_Food.dck', 'Destyn_Turtles.dck', '-f',
                   'Commander', '-seeds', *map(str, seeds), '-c', '180', '-a',
                   'Default', 'Default', 'Default', 'Default']
        log = root / (run + '.log')
        if not (args.resume and log.exists()):
            with log.open('w') as output:
                subprocess.run(command, cwd=args.resource_directory.resolve(), stdout=output,
                               stderr=subprocess.STDOUT, check=True, timeout=240 * len(seeds) + 120)
        detailed = read_games(log.read_text())
        games, tracked = [], []
        for line in log.read_text().splitlines():
            if line.split(':', 1)[0] in categories:
                tracked.append(line)
            match = re.search(r'DragonMind Result: (\{[^\n]+\})', line)
            if match:
                game = json.loads(match.group(1))
                games.append(game)
                traces[label, game['seed']] = detailed[game['seed']]
                tracked = []
        if len(games) != len(seeds) or [game['seed'] for game in games] != seeds:
            raise RuntimeError(run + ': missing or unexpected game results')
        results['runs'][run] = games
        (root / 'seed-expansion-measurements.json').write_text(json.dumps(results, indent=2) + '\n')
        print(run + ': ' + str([game['engine_ms'] for game in games]), flush=True)
    for seed in seeds:
        control = next(g for g in results['runs'][f'group-{group_index + 1}-control'] if g['seed'] == seed)
        candidate = next(g for g in results['runs'][f'group-{group_index + 1}-candidate'] if g['seed'] == seed)
        audit = compare(traces['control', seed], traces['candidate', seed])
        same_trace = audit['trace_match']
        comparison = {'seed': seed, 'control': control, 'candidate': candidate,
                      'tracked_events': len(traces['control', seed]['legacy']), **audit,
                      'outcome_match': all(control.get(k) == candidate.get(k) for k in ('status', 'winner', 'last_logged_turn'))}
        results['comparisons'].append(comparison)
        (root / 'seed-expansion-measurements.json').write_text(json.dumps(results, indent=2) + '\n')
        if not audit['phase_inventory_match'] or not comparison['outcome_match']:
            raise RuntimeError(f'Seed {seed}: behavior mismatch')
        if control['status'] != 'completed' or candidate['status'] != 'completed':
            raise RuntimeError(f'Seed {seed}: incomplete pair; do not report it as a completed-game gain')
control_ms = sum(pair['control']['engine_ms'] for pair in results['comparisons'])
candidate_ms = sum(pair['candidate']['engine_ms'] for pair in results['comparisons'])
results['aggregate'] = {'control_ms': control_ms, 'candidate_ms': candidate_ms,
                        'reduction_percent': 100 * (control_ms - candidate_ms) / control_ms,
                        'faster_pairs': sum(p['candidate']['engine_ms'] < p['control']['engine_ms'] for p in results['comparisons']),
                        'exact_matching_pairs': sum(p['trace_match'] for p in results['comparisons']),
                        'phase_inventory_matching_records': sum(p['full_tracked_records'] for p in results['comparisons'])}
(root / 'seed-expansion-measurements.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results['aggregate']), flush=True)
