#!/usr/bin/env python3
"""Immutable, portable milestone archives. Persistence requires external save acknowledgement.

A verified archive proves bytes and declared completion markers, never rules
correctness or strategic quality. Unknown/in-flight game outcomes stay unknown.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scan(stream, markers=(), destination=None):
    """Bound memory while hashing/copying; detect markers across chunk boundaries."""
    checksum = hashlib.sha256()
    size = 0
    needles = {marker: marker.encode() for marker in markers}
    found = {marker for marker, needle in needles.items() if not needle}
    overlap = max((len(needle) - 1 for needle in needles.values()), default=0)
    tail = b''
    while chunk := stream.read(1024 * 1024):
        checksum.update(chunk)
        size += len(chunk)
        if destination is not None:
            destination.write(chunk)
        window = tail + chunk
        found.update(marker for marker, needle in needles.items() if needle in window)
        tail = window[-overlap:] if overlap else b''
    if set(needles) - found:
        raise ValueError('Missing completion marker')
    return checksum.hexdigest(), size


def file_digest(path):
    with Path(path).open('rb') as stream:
        return scan(stream)[0]


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or p.as_posix() != name:
        raise ValueError('Unsafe archive path: ' + name)
    return name


def verify(path, expected_sha256):
    if file_digest(path) != expected_sha256:
        raise ValueError('Archive SHA256 mismatch')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive member')
        for info in z.infolist():
            safe_name(info.filename)
            if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Only regular files permitted')
        m = json.loads(z.read('MANIFEST.json'))
        if m['format'] != 1 or not m['files']:
            raise ValueError('Invalid manifest')
        if set(names) != set(m['files']) | {'MANIFEST.json'}:
            raise ValueError('Unlisted or missing archive member')
        for name, entry in m['files'].items():
            try:
                with z.open(name) as source:
                    checksum, size = scan(source, entry.get('required_markers', []))
            except zipfile.BadZipFile as error:
                raise ValueError('ZIP CRC failure: ' + name) from error
            if checksum != entry['sha256'] or size != entry['bytes']:
                raise ValueError('Member hash/size mismatch: ' + name)
        return m


def create(root, output, metadata, files, markers=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    markers = markers or {}
    if not files or set(markers) - set(files):
        raise ValueError('Explicit nonempty file list and bound markers required')
    if not metadata.get('milestone') or len(metadata.get('source_commit', '')) != 40:
        raise ValueError('Milestone and exact source commit required')
    entries = {}
    for name in files:
        safe_name(name)
        p = root / name
        if name == 'MANIFEST.json' or name in entries or p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError('Unsafe, reserved or duplicate input')
        with p.open('rb') as source:
            checksum, size = scan(source, markers.get(name, []))
        entries[name] = {'sha256': checksum, 'bytes': size, 'required_markers': markers.get(name, [])}
    manifest = {'format': 1, 'metadata': metadata, 'files': entries,
                'learning_admission': 'Not granted by checkpoint verification'}
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.checkpoint-', dir=output.parent)
    try:
        with os.fdopen(fd, 'w+b') as handle:
            with zipfile.ZipFile(handle, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, entry in entries.items():
                    with (root / name).open('rb') as source, z.open(name, 'w', force_zip64=True) as destination:
                        checksum, size = scan(source, entry['required_markers'], destination)
                    if checksum != entry['sha256'] or size != entry['bytes']:
                        raise ValueError('Source changed while sealing: ' + name)
                z.writestr('MANIFEST.json', json.dumps(manifest, sort_keys=True, indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        checksum = file_digest(temp)
        verify(temp, checksum)
        # Exclusive publication: an existing completed checkpoint is never replaced.
        os.link(temp, output)
        directory_fd = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return {'path': str(output), 'sha256': checksum, 'milestone': metadata['milestone'],
                'persistence': 'local_only_until_external_save_and_readback'}
    finally:
        Path(temp).unlink(missing_ok=True)


def restore(archive, checksum, destination):
    m = verify(archive, checksum)
    dest = Path(destination)
    if dest.exists():
        raise FileExistsError('Restore requires a new destination; preserve existing work')
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.restore-', dir=dest.parent))
    try:
        with zipfile.ZipFile(archive) as z:
            for name in m['files']:
                p = staging / name
                p.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as source, p.open('xb') as destination:
                    checksum, size = scan(source, m['files'][name].get('required_markers', []), destination)
                if checksum != m['files'][name]['sha256'] or size != m['files'][name]['bytes']:
                    raise ValueError('Archive changed during restore: ' + name)
            (staging / 'MANIFEST.json').write_bytes(z.read('MANIFEST.json'))
        # Caller owns destination allocation; never merge restored and live evidence.
        if dest.exists():
            raise FileExistsError(dest)
        os.rename(staging, dest)
    finally:
        if staging.exists():
            import shutil
            shutil.rmtree(staging)
    return m


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    c = sub.add_parser('create')
    c.add_argument('--root', type=Path, required=True)
    c.add_argument('--output', type=Path, required=True)
    c.add_argument('--spec', type=Path, required=True, help='JSON metadata, files and optional markers')
    for action in ('verify', 'restore'):
        q = sub.add_parser(action)
        q.add_argument('--archive', type=Path, required=True)
        q.add_argument('--sha256', required=True)
        if action == 'restore':
            q.add_argument('--destination', type=Path, required=True)
    a = p.parse_args()
    if a.action == 'create':
        spec = json.loads(a.spec.read_text())
        result = create(a.root, a.output, spec['metadata'], spec['files'], spec.get('markers'))
    elif a.action == 'verify':
        result = verify(a.archive, a.sha256)
    else:
        result = restore(a.archive, a.sha256, a.destination)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
