"""Overlay one evidence component on its exact verified executable; no policy change."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
BASE = '8a323239ba4fdc2baeb9fc91318370f6c8f98b45cdb668e3f418ed24786321f8'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1024 * 1024):
            result.update(data)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--component', choices=('writer', 'recorder'), default='writer')
    args = parser.parse_args()
    expected = BASE if args.component == 'writer' else '0d1ee30d3bba14e9ff71a9d1363abf5528b474df027e1c593b7c36ea10083e05'
    if digest(args.base) != expected:
        raise ValueError('Exact verified typed-recorder executable required')
    if args.output.exists():
        raise FileExistsError(args.output)
    if Path('/workspace') in args.output.resolve().parents:
        raise ValueError('Active build output must be outside synchronized workspace')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    component = 'DurableEvidence' if args.component == 'writer' else 'EngineEvidence'
    source = ROOT / ('pilot-src/forge/ai/bridge/' + component + '.java')
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
        root = Path(temporary)
        subprocess.run(['java', '-XX:-UsePerfData', '-m', 'jdk.compiler/com.sun.tools.javac.Main',
                        '-cp', str(args.base.resolve()), '-d', str(root), str(source)], check=True)
        classes = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*.class')}
        nested = 'Stream' if args.component == 'writer' else 'Call'
        if set(classes) != {'forge/ai/bridge/' + component + '.class',
                            'forge/ai/bridge/' + component + '$' + nested + '.class'}:
            raise ValueError('Unexpected writer overlay classes')
        staged = root / 'streaming-finalizer.jar'
        with zipfile.ZipFile(args.base) as old, zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():
                new.writestr(entry, classes.get(entry.filename, old.read(entry.filename)))
        with zipfile.ZipFile(args.base) as old, zipfile.ZipFile(staged) as new:
            if new.testzip() is not None or set(old.namelist()) != set(new.namelist()):
                raise ValueError('Invalid overlay executable')
            for name in old.namelist():
                if name not in classes and old.read(name) != new.read(name):
                    raise ValueError('Unrelated executable entry changed: ' + name)
        with staged.open('rb') as handle:
            os.fsync(handle.fileno())
        os.link(staged, args.output)
        directory = os.open(args.output.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    manifest = {'base_sha256': expected, 'component': args.component, 'sha256': digest(args.output), 'classes': sorted(classes),
                'source_sha256': digest(source), 'builder_sha256': digest(Path(__file__)),
                'other_entries_byte_identical': True, 'policy_changed': False, 'promotion': False}
    args.output.with_suffix('.build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
