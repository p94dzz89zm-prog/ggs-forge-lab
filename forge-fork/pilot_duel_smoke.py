#!/usr/bin/env python3
"""Two-seat stock/v1 integration comparison. Not a pod performance benchmark."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def run(engine, output, seed, timeout, mode):
    directory = output / mode
    directory.mkdir(parents=True, exist_ok=True)
    jar = engine / 'forge-gui-desktop-2.0.15-jar-with-dependencies.jar'
    flags = [] if mode == 'stock' else ['-Dforge.ai.ggsPilotPlayer=Ai(1)-GGS_Current']
    cmd = ['java', '-Xmx1536m', '-Djava.awt.headless=true',
           '-Dforge.audit.directory=' + str(directory / 'audit'), *flags, '-jar', str(jar),
           'sim', '-D', str(ROOT / 'decks'), '-d', 'GGS_Current.dck', 'Jaymie_Ezio.dck',
           '-f', 'Commander', '-a', 'Default', 'Default', '-n', '1', '-s', str(seed), '-c', str(timeout)]
    start = time.monotonic()
    with (directory / 'game.log').open('w') as log:
        try:
            rc = subprocess.run(cmd, cwd=engine, stdout=log, stderr=subprocess.STDOUT,
                                timeout=timeout + 45).returncode
        except subprocess.TimeoutExpired:
            rc = -1
            log.write('\nHARNESS_PROCESS_TIMEOUT\n')
    text = (directory / 'game.log').read_text()
    errors = re.search(r'(?:(?:[A-Za-z_]\w*\.)+[A-Za-z_]\w*(?:Exception|Error)\b|Exception in thread|StackOverflowError|OutOfMemoryError)', text)
    results = re.findall(r'^Game Result: Game \d+ ended in (\d+) ms\. (.+?) has won!', text, re.M)
    outcomes = set(re.findall(r'^Game Outcome: (.+?) has (?:won|lost)\b', text, re.M))
    status = ('process_timeout' if rc == -1 else 'timeout' if 'Stopping slow match as draw' in text
              else 'engine_error' if rc or errors else 'completed' if len(results) == 1 and len(outcomes) == 2
              else 'unresolved')
    audit = directory / 'audit' / 'evaluation-seat-0.jsonl'
    decisions = [json.loads(line) for line in audit.read_text().splitlines()] if audit.exists() else []
    policy = [d for d in decisions if d.get('decision', '').startswith('GgsNinjutsu:')]
    record = {'mode': mode, 'seed': seed, 'status': status, 'returncode': rc,
              'winner': results[0][1] if status == 'completed' else None,
              'wall_seconds': round(time.monotonic() - start, 3), 'command': cmd,
              'engine_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
              'log_sha256': hashlib.sha256((directory / 'game.log').read_bytes()).hexdigest(),
              'new_policy_evaluations': len(policy),
              'new_policy_return_payments': sum('payReturn=' in d['decision'] for d in policy)}
    (directory / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--seed', type=int, default=20261002)
    p.add_argument('--timeout', type=int, default=90)
    a = p.parse_args()
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run, a.engine.resolve(), out, a.seed, a.timeout, mode) for mode in ['stock', 'improved']]
        records = []
        for future in concurrent.futures.as_completed(futures):
            r = future.result(); records.append(r)
            print(r['mode'], r['status'], 'policy evaluations', r['new_policy_evaluations'], flush=True)
    (out / 'summary.json').write_text(json.dumps(records, indent=2) + '\n')

if __name__ == '__main__':
    main()
