"""Small immutable executable overlay, bound to exact base and restored JAR hashes.

This transports changed entries only. The pinned base must remain independently
archived. It never edits that base or overwrites a restored executable.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def publish(staged, output):
    with staged.open('rb') as stream:
        os.fsync(stream.fileno())
    os.link(staged, output)  # Exclusive publication; never replace evidence.
    fd = os.open(output.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def create(base, target, output):
    base_hash, target_hash = digest(base), digest(target)
    with zipfile.ZipFile(base) as old, zipfile.ZipFile(target) as new:
        if old.namelist() != new.namelist() or len(set(old.namelist())) != len(old.namelist()):
            raise ValueError('Entry inventory/order changed or duplicate names')
        changes = {name: new.read(name) for name in old.namelist() if old.read(name) != new.read(name)}
    manifest = {'format': 1, 'base_sha256': base_hash, 'target_sha256': target_hash,
                'entries': {name: hashlib.sha256(data).hexdigest() for name, data in changes.items()}}
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / 'delta.zip'
        with zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json', json.dumps(manifest, sort_keys=True))
            for name, data in changes.items():
                archive.writestr('entries/' + name, data)
        # ZIP metadata/encoding differences cannot silently yield a usable delta.
        restored = Path(temporary) / 'restored.jar'
        restore(base, staged, restored)
        if digest(base) != base_hash or digest(target) != target_hash:
            raise ValueError('Executable mutated while creating delta')
        publish(staged, output)
    return manifest


def restore(base, delta, output):
    with zipfile.ZipFile(delta) as archive:
        manifest = json.loads(archive.read('manifest.json'))
        if manifest['format'] != 1 or digest(base) != manifest['base_sha256']:
            raise ValueError('Wrong base executable')
        names = archive.namelist()
        expected = {'manifest.json'} | {'entries/' + name for name in manifest['entries']}
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError('Unexpected delta members')
        changes = {name: archive.read('entries/' + name) for name in manifest['entries']}
        for name, data in changes.items():
            if hashlib.sha256(data).hexdigest() != manifest['entries'][name]:
                raise ValueError('Changed executable entry: ' + name)
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staged = Path(temporary) / 'restored.jar'
        with zipfile.ZipFile(base) as old, zipfile.ZipFile(staged, 'w', zipfile.ZIP_DEFLATED) as new:
            if len(set(old.namelist())) != len(old.namelist()) or not set(changes) <= set(old.namelist()):
                raise ValueError('Invalid base entry inventory')
            for entry in old.infolist():
                new.writestr(entry, changes.get(entry.filename, old.read(entry.filename)))
        if digest(staged) != manifest['target_sha256']:
            raise ValueError('Restored executable checksum differs')
        publish(staged, output)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('create', 'restore'))
    parser.add_argument('base', type=Path)
    parser.add_argument('input', type=Path, help='target JAR for create; delta ZIP for restore')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(globals()[args.mode](args.base, args.input, args.output), sort_keys=True))
