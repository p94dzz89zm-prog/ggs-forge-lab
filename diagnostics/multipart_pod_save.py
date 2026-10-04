"""Incremental private pod archives below the Library per-file limit.

The checkpoint tar contains protocol, attempts and a recovery manifest. Fetch
each manifest chunk, verify its SHA256, concatenate chunks in order, and safely
extract each resulting tar beneath the checkpoint's parent to recover attempts.
"""
import hashlib, io, json, tarfile
from pathlib import Path

CHUNK_BYTES = 64 * 1024 * 1024

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n')
    temp.replace(path)

def save_checkpoint(root, destination, records, upload, helper, identity=None):
    state_path = root/'multipart-save.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'segments': []}
    covered = {folder for segment in state['segments'] for folder in segment['folders']}
    missing = [record for record in records if record['folder'] not in covered]
    if missing:
        number = len(state['segments']) + 1
        archive_path = root.parent/f'GGS_Private_Pod_v17_Segment_{number:03d}.tar.gz'
        with tarfile.open(archive_path, 'w:gz', compresslevel=1) as archive:
            for record in missing:
                folder = Path(record['folder'])
                assert not folder.is_absolute() and '..' not in folder.parts
                archive.add(root/folder, arcname=root.name+'/'+str(folder))
        with tarfile.open(archive_path, 'r:gz') as archive:
            assert sum(m.name.endswith('/summary.json') for m in archive.getmembers()) == len(missing)
            for member in archive.getmembers():
                assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                if member.isfile():
                    with archive.extractfile(member) as source:
                        while source.read(1024*1024):
                            pass
        segment = {'folders': [r['folder'] for r in missing],
                   'archive_sha256': digest(archive_path), 'chunks': []}
        with archive_path.open('rb') as source:
            while data := source.read(CHUNK_BYTES):
                path = archive_path.with_name(archive_path.name+f'.part{len(segment["chunks"])+1:03d}')
                path.write_bytes(data)
                segment['chunks'].append({'file_name': path.name, 'bytes': len(data),
                                          'sha256': digest(path), 'local_path': str(path)})
        state['segments'].append(segment)
        write_json(state_path, state)
        # The byte-identical chunks now hold the archive; keep only one local copy.
        archive_path.unlink()
    for segment in state['segments']:
        for chunk in segment['chunks']:
            if 'saved' not in chunk:
                chunk['saved'] = upload(helper, [{'local_path': chunk['local_path'],
                    'purpose': 'create_library_file', 'library_artifact_type': 'other'}])[0]
                write_json(state_path, state)
    manifest = {'format': 'ggs-private-multipart-v1',
                'recovery': 'Download chunks by library_file_id, verify chunk hashes, concatenate per segment, verify archive hash, validate relative tar paths and extract under checkpoint parent. Never overwrite completed records.',
                'segments': [{**s, 'chunks': [{k:v for k,v in c.items() if k!='local_path'}
                                            for c in s['chunks']]} for s in state['segments']]}
    with tarfile.open(destination, 'w:gz') as archive:
        for name, value in [('protocol.json', json.loads((root/'protocol.json').read_text())),
                            ('attempts.json', records), ('multipart-manifest.json', manifest)]:
            data = (json.dumps(value, indent=2)+'\n').encode()
            member = tarfile.TarInfo(root.name+'/'+name); member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        for name in ('finished.json', 'selected.json', 'integrity-review.json', 'integrity-save.json', 'report-save.json'):
            if (root/name).exists():
                archive.add(root/name, arcname=root.name+'/'+name)
    request = {'local_path': str(destination), 'purpose': 'create_library_file',
               'library_artifact_type': 'other'}
    if identity:
        request = {'local_path': str(destination), 'purpose': 'replace_library_file',
                   'library_file_id': identity['library_file_id'],
                   'expected_current_version': identity['current_version_number'],
                   'version_reason': f'{len(records)} attempts; multipart recovery manifest'}
    return upload(helper, [request])[0]
