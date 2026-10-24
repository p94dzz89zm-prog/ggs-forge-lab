"""Three bounded native controls; never complete-game certification or training."""
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
    a.runtime = a.runtime.resolve(); a.patched = a.patched.resolve(); a.logs = a.logs.resolve()
    a.logs.mkdir(exist_ok=False, parents=True)
    root = Path(__file__).resolve().parent
    inputs = [a.runtime/'pilot-recovery-10.jar', a.runtime/'testng-7.10.2.jar',
              a.runtime/'fixture-classes/forge/ai/AITest.class', a.patched]
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    expected = json.loads((a.runtime/'RUNTIME.json').read_text())['files']
    for path in inputs[:-1]:
        if digest(path) != expected[path.relative_to(a.runtime).as_posix()]:
            raise ValueError('Runtime dependency hash mismatch')
    build = json.loads(a.patched.with_suffix('.build.json').read_text())
    if digest(a.patched) != build['output_sha256'] or digest(inputs[0]) != build['base_sha256']:
        raise ValueError('Overlay provenance mismatch')
    cp = ':'.join(map(str, [inputs[0], inputs[1], a.runtime/'fixture-classes']))
    classes = a.logs/'classes'
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-cp', cp, '-d', str(classes),
                    str(root/'RegressionLauncher.java'), str(root/'MulliganRoundRegression.java'),
                    str(root/'pilot-src/forge/game/mulligan/HouseMulligan.java')], check=True)
    results = dict(seed=56, new_natural_games=0, full_game_rules_approved=False,
                   input_sha256={str(x): digest(x) for x in inputs}, controls=[])
    for label, jar, policy in [('original-standard', inputs[0], 'standard'),
                               ('patched-standard', a.patched, 'standard'), ('patched-house', a.patched, 'house')]:
        home = a.logs/('home-'+label); home.mkdir(); start = time.monotonic()
        with (a.logs/(label+'.log')).open('x') as stream:
            try:
                rc = subprocess.run(['java', '-XX:-UsePerfData', '-Xmx1536m', '-Djava.awt.headless=true',
                                     '-Duser.home='+str(home), '-cp', ':'.join(map(str, [jar, inputs[1],
                                     a.runtime/'fixture-classes', classes])), 'RegressionLauncher',
                                     'MulliganRoundRegression', policy], cwd=a.runtime/'engine', stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=70).returncode
            except subprocess.TimeoutExpired:
                rc = None
        text = (a.logs/(label+'.log')).read_text()
        ok = ((rc == 1 and 'hand changed before all round declarations: prompt=1' in text)
              if label == 'original-standard' else
              (rc == 0 and 'PASS native round declarations, policy='+policy in text))
        results['controls'].append(dict(label=label, returncode=rc, expected_result_observed=ok,
                                        seconds=round(time.monotonic()-start, 2)))
        results['inputs_unchanged'] = all(digest(x) == results['input_sha256'][str(x)] for x in inputs)
        (a.logs/'native-results.json').write_text(json.dumps(results, indent=2)+'\n')
        if not ok or not results['inputs_unchanged']:
            raise RuntimeError('Native control failed; preserve logs')
    print('NATIVE_ROUND_VALIDATION_COMPLETE')


if __name__ == '__main__':
    main()
