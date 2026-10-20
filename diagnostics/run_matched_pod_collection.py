"""Checkpoint matched, seat-balanced pod games; retain every attempt privately."""
import argparse, concurrent.futures, fcntl, hashlib, json, random, shutil, sys, tarfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dragonmind import batch
from run_games import ROOT, validate_deck
from analyze_five_pod_games import summarize

VALID = {'completed', 'completed_draw'}
VARIANTS = {'apex': 'GGS_Apex_War_Form_Current', 'layered': 'GGS_Layered_v1'}

def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)

def attempt(engine, jar, out, name, rotation, seed, number, timeout, metadata):
    folder = out / name / f'rotation{rotation}' / f'seed{seed}' / f'attempt{number}'
    folder.mkdir(parents=True, exist_ok=False)
    write_json(folder / 'metadata.json', metadata[name])
    started = time.monotonic()
    rows = batch(engine, jar, folder, VARIANTS[name], rotation, [seed], timeout,
                 True, True, 'parallel', 'throughput')
    write_json(folder / 'summary.json', rows)
    write_json(folder / 'performance.json', {'wall_seconds': time.monotonic()-started,
               'completed': int(rows[0]['status'] in VALID)})
    if rows[0]['status'] in VALID:
        write_json(folder / 'analysis.json', summarize(folder, expected_games=1))
    # Preserve raw private audits losslessly before reclaiming generated JSONL space.
    audit = folder / 'audit'
    if audit.exists():
        files = sorted(p for p in audit.rglob('*') if p.is_file())
        expected = {str(p.relative_to(folder)): p.stat().st_size for p in files}
        archive = folder / 'private-audits.tar.gz'
        with tarfile.open(archive, 'w:gz', compresslevel=1) as stream:
            stream.add(audit, arcname='audit')
        with tarfile.open(archive, 'r:gz') as stream:
            actual = {m.name: m.size for m in stream.getmembers() if m.isfile()}
            assert actual == expected
            # Read every compressed member to verify archive integrity before removal.
            for member in stream.getmembers():
                if member.isfile():
                    source = stream.extractfile(member)
                    while source.read(1024*1024):
                        pass
        write_json(folder / 'audit-archive.json', {'bytes': archive.stat().st_size,
                   'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                   'files': len(expected), 'uncompressed_bytes': sum(expected.values())})
        shutil.rmtree(audit)  # Only this attempt's newly generated, verified archived data.
    return {'deck': name, 'rotation': rotation, 'seed': seed, 'attempt': number,
            'status': rows[0]['status'], 'winner': rows[0].get('winner'),
            'engine_ms': rows[0].get('engine_ms'), 'folder': str(folder.relative_to(out))}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--jar', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--first-seed', type=int, default=20261038)
    parser.add_argument('--seeds', type=int, default=25)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--resume', action='store_true', help='Resume checkpointed attempts without replacing completed data')
    args = parser.parse_args()
    assert args.seeds > 0 and args.workers > 0 and args.timeout > 0
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=args.resume)
    lock = (out/'runner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.resume and (out/'finished.json').exists():
        print((out/'finished.json').read_text()); return
    jar = args.jar.resolve(); engine = args.engine.resolve()
    for variant in [*VARIANTS.values(), 'Jaymie_Ezio', 'Gabe_Food', 'Destyn_Turtles']:
        validate_deck(ROOT / 'decks' / (variant+'.dck'))
    metadata = {}
    for name, variant in VARIANTS.items():
        metadata[name] = {'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
            'deck_sha256': {v: hashlib.sha256((ROOT/'decks'/(v+'.dck')).read_bytes()).hexdigest()
                           for v in [variant, 'Jaymie_Ezio', 'Gabe_Food', 'Destyn_Turtles']},
            'configuration': {'workers': args.workers, 'batch_size': 1, 'timeout': args.timeout,
                              'audit': True, 'stock': False, 'gc': 'parallel', 'jit': 'throughput'}}
    pairs = [(r, s) for s in range(args.first_seed, args.first_seed+args.seeds) for r in range(4)]
    random.Random(20261004).shuffle(pairs)
    jobs = [(n, r, s, 1) for i, (r, s) in enumerate(pairs)
            for n in (('apex', 'layered') if i % 2 == 0 else ('layered', 'apex'))]
    protocol = {'metadata': metadata, 'planned_games_per_deck': len(pairs),
        'pairs': pairs, 'retry_policy': 'One identical-settings retry for every invalid slot, after initial collection; no substitute seeds',
        'private_audits': 'Losslessly compressed per attempt after analysis and integrity verification'}
    if args.resume:
        assert json.loads((out/'protocol.json').read_text()) == json.loads(json.dumps(protocol)), 'Resume protocol/engine/deck mismatch'
    else:
        write_json(out/'protocol.json', protocol)
    started = time.monotonic()
    records = json.loads((out/'attempts.json').read_text()) if args.resume and (out/'attempts.json').exists() else []
    done = {(r['deck'],r['rotation'],r['seed'],r['attempt']) for r in records}
    jobs = [j for j in jobs if j not in done]
    def phase(work):
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending = [pool.submit(attempt, engine, jar, out, n, r, s, a, args.timeout, metadata)
                       for n, r, s, a in work]
            for future in concurrent.futures.as_completed(pending):
                records.append(future.result())
                write_json(out/'attempts.json', records)
                counts = {n: sum(x['deck']==n and x['status'] in VALID for x in records) for n in VARIANTS}
                print(json.dumps({'attempts_finished': len(records), 'valid_attempts': counts,
                                  'latest': records[-1], 'wall_seconds': round(time.monotonic()-started, 1)}), flush=True)
    phase(jobs)
    retries = [(x['deck'], x['rotation'], x['seed'], 2) for x in records
               if x['attempt']==1 and x['status'] not in VALID
               and (x['deck'],x['rotation'],x['seed'],2) not in done]
    phase(retries)
    selected = {(x['deck'], x['rotation'], x['seed']): x for x in sorted(records,key=lambda r:r['attempt'])}
    write_json(out/'selected.json', list(selected.values()))
    write_json(out/'finished.json', {'wall_seconds': time.monotonic()-started,
        'attempts': len(records), 'scheduled_slots': 2*len(pairs),
        'retries': sum(x['attempt']==2 for x in records),
        'wall_seconds_meaning': 'Current invocation elapsed time; earlier time excluded when resumed',
        'valid_selected_by_deck': {n: sum(x['deck']==n and x['status'] in VALID for x in selected.values()) for n in VARIANTS}})

if __name__ == '__main__':
    main()
