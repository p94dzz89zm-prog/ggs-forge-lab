"""Measure packaged-runner throughput for the same four games at one/two workers."""
from trace_compare import read_games, compare
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time
parser = argparse.ArgumentParser(description=__doc__)
for name in ['engine', 'jar', 'output_directory']:
    parser.add_argument(name, type=Path)
parser.add_argument('--seed', type=int, default=20261013)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
root = args.output_directory.resolve()
root.mkdir(parents=True, exist_ok=True)
categories = {'Turn', 'Phase', 'Add To Stack', 'Resolve Stack', 'Damage', 'Combat', 'Life'}
results = {'seed': args.seed, 'seeds': 4, 'batch_size': 2,
           'jar_sha256': hashlib.sha256(args.jar.read_bytes()).hexdigest(), 'runs': []}
reference = None
for workers in [2, 1]:
    out = root / f'workers-{workers}'
    command = [sys.executable, str(repo / 'dragonmind.py'), '--engine', str(args.engine.resolve()),
               '--jar', str(args.jar.resolve()), '--seed', str(args.seed), '--seeds', '4',
               '--rotations', '0', '--workers', str(workers), '--batch-size', '2', '--timeout',
               '180', '--stock', '--output', str(out)]
    print(f'Starting {workers} workers', flush=True)
    start = time.monotonic()
    with (root / f'workers-{workers}.log').open('w') as output:
        subprocess.run(command, cwd=repo, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=1000)
    elapsed = time.monotonic() - start
    performance = json.loads((out / 'performance.json').read_text())
    if performance['completed'] != 4:
        raise RuntimeError(f'{workers} workers: incomplete games')
    traces = {}
    for log in out.glob('*.log'):
        traces.update(read_games(log.read_text()))
    if len(traces) != 4:
        raise RuntimeError('Missing trace results')
    audits = {}
    if reference is None:
        reference = traces
    else:
        for seed, game in traces.items():
            audits[seed] = compare(reference[seed], game)
            if not audits[seed]['phase_inventory_match'] or any(
                    reference[seed]['game'].get(key) != game['game'].get(key)
                    for key in ('status', 'winner', 'last_logged_turn')):
                raise RuntimeError('Worker-count behavior mismatch')
    record = {'workers': workers, 'wall_seconds': elapsed, 'games_per_minute': 240 / elapsed,
              'performance': performance, 'tracked_events': sum(t['count'] for t in traces.values()),
              'comparisons_against_two_workers': audits}
    results['runs'].append(record)
    (root / 'worker-throughput-measurements.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(record), flush=True)
two, one = results['runs']
results['throughput_ratio_two_to_one'] = two['games_per_minute'] / one['games_per_minute']
results['limited_sample'] = True
(root / 'worker-throughput-measurements.json').write_text(json.dumps(results, indent=2) + '\n')
