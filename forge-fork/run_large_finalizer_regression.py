"""Compare the actual old and repaired writers with a stream larger than heap."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def run(old, new, output):
    output = Path(output).resolve()
    if Path('/workspace') in output.parents:
        raise ValueError('Regression evidence must be outside workspace')
    output.mkdir(parents=True, exist_ok=True)
    classes = output / 'classes'
    classes.mkdir()
    source = Path(__file__).with_name('LargeEvidenceRegression.java')
    subprocess.run(['java', '-XX:-UsePerfData', '-m', 'jdk.compiler/com.sun.tools.javac.Main',
                    '-cp', str(new), '-d', str(classes), str(source)], check=True)
    results = {}
    for name, jar in [('original', old), ('streaming', new)]:
        target = output / name
        process = subprocess.run(['java', '-XX:-UsePerfData', '-Xmx64m', '-cp',
                                  str(classes) + ':' + str(jar), 'LargeEvidenceRegression', str(target)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        (output / (name + '.log')).write_bytes(process.stdout)
        manifests = list(target.rglob('*.evidence.json'))
        results[name] = {'returncode': process.returncode, 'completion_manifests': len(manifests)}
        if name == 'original':
            assert process.returncode != 0 and b'OutOfMemoryError' in process.stdout
            assert not manifests, 'Failed original must not appear sealed'
        else:
            assert process.returncode == 0 and b'PASS large durable evidence finalization' in process.stdout
            assert len(manifests) == 1
            manifest = json.loads(manifests[0].read_text())
            assert manifest['completion_marker'] == 'DRAGONMIND_EVIDENCE_COMPLETE'
            assert len(manifest['streams']) == 1
            receipt = manifest['streams'][0]
            stream = target / receipt['file']
            checksum = hashlib.sha256()
            rows = 0
            with stream.open('rb') as handle:
                while chunk := handle.read(1024 * 1024):
                    checksum.update(chunk)
                    rows += chunk.count(b'\n')
            assert checksum.hexdigest() == receipt['sha256']
            assert stream.stat().st_size == receipt['bytes'] >= 96 * 1024 * 1024
            assert rows == receipt['records'] == 384
            results[name].update(receipt)
    results['rules_approval'] = False
    (output / 'comparison.json').write_text(json.dumps(results, indent=2) + '\n')
    print('PASS old writer OOM safely unsealed; repaired writer seals 96MiB under64MiB heap')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    run(args.old.resolve(), args.new.resolve(), args.output)
