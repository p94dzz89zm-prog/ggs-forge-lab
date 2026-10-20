"""Verify the entire source-only Git index and every source file against a manifest."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess


def verify(root):
    root = Path(root).resolve()
    manifest_name = 'SOURCE_PROVENANCE.json'
    manifest = json.loads((root/manifest_name).read_text())
    if manifest.get('format') != 2 or type(manifest.get('format')) is not int:
        raise ValueError('Unsupported source manifest')
    entries = manifest['files']
    if not isinstance(entries, dict) or not entries:
        raise ValueError('Empty source inventory')
    tracked = set(subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0'))-{''}
    if tracked != set(entries) | {manifest_name}:
        raise ValueError('Git file inventory differs from complete expected manifest')
    for name, entry in entries.items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name:
            raise ValueError('Unsafe manifest path')
        path = root/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError('Missing or unsafe source: '+name)
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            while chunk := stream.read(1024*1024):digest.update(chunk)
        if digest.hexdigest() != entry['sha256']:
            raise ValueError('Source hash changed: '+name)
    return dict(verified_files=len(tracked), source_inventory_verified=True,
                complete_game_rules_approved=False)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',nargs='?',default=Path(__file__).resolve().parent)
    print(json.dumps(verify(p.parse_args().root),sort_keys=True))
