"""Exclusive per-side snapshots checked against ORIGINAL finalization hashes.

Local snapshots require external save/readback. They never approve gameplay,
repair changed evidence, or permit recapture during interrupted resume.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
import milestone_checkpoint as checkpoint


def evidence_files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob('*')
            if p.is_file() and p.suffix in ('.json', '.jsonl', '.log', '.partial')
            and 'runtime-home' not in p.parts}


def verify_live(root, entry):
    root = Path(root).resolve()
    expected = entry.get('evidence_sha256')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Missing finalized evidence hashes')
    if evidence_files(root) != set(expected):
        raise ValueError('Missing or unbound evidence file')
    for name, want in expected.items():
        checkpoint.safe_name(name)
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Unsafe finalized evidence path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != want:
            raise ValueError('Saved evidence changed: ' + name)


def finalized_entry(entry):
    return {k: v for k, v in entry.items() if k != 'immutable_capture'}


def verify_capture(pair_root, entry, protocol):
    receipt = entry.get('immutable_capture')
    if not isinstance(receipt, dict):
        raise ValueError('Missing immutable capture; never recapture on resume')
    name = checkpoint.safe_name(receipt['relative_path'])
    pair_root = Path(pair_root).resolve()
    archive = pair_root / name
    if archive.is_symlink() or not archive.resolve().is_relative_to(pair_root):
        raise ValueError('Unsafe capture archive path')
    manifest = checkpoint.verify(archive, receipt['sha256'])
    expected = entry['evidence_sha256']
    if set(manifest['files']) != {'evidence/' + n for n in expected} | {'finalization.json', 'protocol.json'}:
        raise ValueError('Capture inventory differs from original finalization')
    with zipfile.ZipFile(archive) as z:
        if json.loads(z.read('finalization.json')) != finalized_entry(entry):
            raise ValueError('Capture finalization differs from original journal')
        if json.loads(z.read('protocol.json')) != protocol:
            raise ValueError('Capture protocol differs from frozen inputs')
        for n, want in expected.items():
            if manifest['files']['evidence/' + n]['sha256'] != want:
                raise ValueError('Capture differs from ORIGINAL finalized hash: ' + n)
    return manifest


def capture(pair_root, entry, protocol, source_commit):
    pair_root = Path(pair_root).resolve()
    label = entry['label']
    if label not in ('baseline', 'candidate') or entry.get('status') != 'saved' or not entry.get('complete'):
        raise ValueError('Only finalized complete sides can be captured')
    if 'immutable_capture' in entry:
        raise ValueError('Existing capture must be verified, never replaced')
    root = pair_root / label
    verify_live(root, entry)
    frozen = json.loads(json.dumps(finalized_entry(entry)))
    output = pair_root / 'captures' / (label + '.zip')
    with tempfile.TemporaryDirectory(prefix='side-capture-', dir=pair_root) as td:
        staging = Path(td)
        for n, want in frozen['evidence_sha256'].items():
            data = (root / n).read_bytes()
            if hashlib.sha256(data).hexdigest() != want:
                raise ValueError('Evidence changed during capture: ' + n)
            dest = staging / 'evidence' / n
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        (staging / 'finalization.json').write_text(json.dumps(frozen, sort_keys=True))
        (staging / 'protocol.json').write_text(json.dumps(protocol, sort_keys=True))
        files = sorted(p.relative_to(staging).as_posix() for p in staging.rglob('*') if p.is_file())
        result = checkpoint.create(staging, output,
            {'milestone': 'immutable-side-' + label, 'source_commit': source_commit,
             'rules_approval': False}, files)
    receipt = {'relative_path': output.relative_to(pair_root).as_posix(),
               'sha256': result['sha256'], 'persistence': result['persistence']}
    verify_capture(pair_root, {**frozen, 'immutable_capture': receipt}, protocol)
    verify_live(root, frozen)
    return receipt
