"""Bounded actual-service regression over a hash-bound integrated runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--patched', type=Path, required=True)
    p.add_argument('--logs', type=Path, required=True)
    a = p.parse_args()
    runtime, jar, logs = a.runtime.resolve(), a.patched.resolve(), a.logs.resolve()
    logs.mkdir(parents=True, exist_ok=False)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    build = json.loads(jar.with_suffix('.build.json').read_text())
    if digest(jar) != build['output_sha256'] or not build['london_zero_card_limit']:
        raise ValueError('Verified integrated build required')
    dependencies = json.loads((runtime/'RUNTIME.json').read_text())['files']
    for name in ['testng-7.10.2.jar', 'fixture-classes/forge/ai/AITest.class']:
        if digest(runtime/name) != dependencies[name]: raise ValueError('Fixture dependency hash mismatch')
    root = Path(__file__).resolve().parent; classes = logs/'classes'
    cp = ':'.join(map(str, [jar, runtime/'testng-7.10.2.jar', runtime/'fixture-classes']))
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-cp', cp, '-d', str(classes),
                    str(root/'RegressionLauncher.java'), str(root/'MulliganServiceRegression.java')], check=True)
    result = dict(engine_sha256=digest(jar), seed=57, full_game_rules_approved=False, controls=[])
    for mode in ['standard', 'cap', 'house']:
        home = logs/('home-'+mode); home.mkdir(); start = time.monotonic()
        with (logs/(mode+'.log')).open('x') as stream:
            try:
                rc = subprocess.run(['java', '-Xmx1536m', '-Djava.awt.headless=true', '-Duser.home='+str(home),
                                     *(['-Ddragonmind.houseProfile=ggs-house-v1'] if mode == 'house' else []),
                                     '-cp', cp+':'+str(classes), 'RegressionLauncher', 'MulliganServiceRegression', mode],
                                     cwd=runtime/'engine', stdout=stream, stderr=subprocess.STDOUT, timeout=70).returncode
            except subprocess.TimeoutExpired:
                rc = None
        text = (logs/(mode+'.log')).read_text()
        ok = rc == 0 and 'PASS full mulligan service policy='+mode in text and digest(jar) == result['engine_sha256']
        result['controls'].append(dict(mode=mode, returncode=rc, passed=ok, seconds=round(time.monotonic()-start, 2)))
        (logs/'native-results.json').write_text(json.dumps(result, indent=2)+'\n')
        if not ok: raise RuntimeError('Native control failed; preserve evidence')
    print('FULL_SERVICE_NATIVE_COMPLETE')


if __name__ == '__main__': main()
