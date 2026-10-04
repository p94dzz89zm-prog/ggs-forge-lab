import hashlib, json, tarfile, tempfile, unittest
from pathlib import Path
import multipart_pod_save as saving

class MultipartRecoveryTest(unittest.TestCase):
    def test_damaged_private_audit_is_rejected_before_upload(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'collection';root.mkdir()
            (root/'protocol.json').write_text('{}')
            folder=root/'attempt';folder.mkdir()
            (folder/'summary.json').write_text('[]')
            (folder/'private-audits.tar.gz').write_bytes(b'truncated')
            (folder/'audit-archive.json').write_text(json.dumps({'bytes':20,'sha256':'original'}))
            with self.assertRaisesRegex(ValueError,'integrity'):
                saving.save_checkpoint(root,base/'index.tar.gz',[{'folder':'attempt'}],
                    lambda *args:self.fail('Damaged records must not be uploaded'),None)

    def test_symlink_cannot_be_archived(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'collection';root.mkdir()
            folder=root/'attempt';folder.mkdir()
            (folder/'link').symlink_to(base)
            with self.assertRaisesRegex(ValueError,'unsupported'):
                saving.validate_attempt(root,'attempt')

    def test_changed_pending_chunk_is_rejected_on_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);root=base/'collection';root.mkdir()
            (root/'protocol.json').write_text('{}')
            folder=root/'attempt';folder.mkdir();(folder/'summary.json').write_text('[]')
            def interrupted(*args):raise RuntimeError('transfer failed')
            with self.assertRaises(RuntimeError):
                saving.save_checkpoint(root,base/'index.tar.gz',[{'folder':'attempt'}],interrupted,None)
            state=json.loads((root/'multipart-save.json').read_text())
            Path(state['segments'][0]['chunks'][0]['local_path']).write_bytes(b'damaged')
            with self.assertRaisesRegex(ValueError,'chunk changed'):
                saving.save_checkpoint(root,base/'index.tar.gz',[{'folder':'attempt'}],
                    lambda *args:self.fail('Changed chunk must not be uploaded'),None)

    def test_recovery_and_incremental_saves(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); root=base/'collection'; root.mkdir()
            (root/'protocol.json').write_text('{}')
            records=[]; calls=[]
            def upload(helper, requests):
                calls.extend(requests)
                return [{'status':'succeeded','local_metadata_applied':True,
                         'library_file_id':str(len(calls)), 'current_version_number':0}]
            old=saving.CHUNK_BYTES; saving.CHUNK_BYTES=100
            try:
                for number in range(2):
                    folder=root/f'attempt{number}'; folder.mkdir()
                    (folder/'summary.json').write_text('[]')
                    (folder/'private.log').write_text('retained private data '+str(number))
                    records.append({'folder':folder.name})
                    saving.save_checkpoint(root,base/'index.tar.gz',records,upload,None)
                with tarfile.open(base/'index.tar.gz') as archive:
                    manifest=json.load(archive.extractfile('collection/multipart-manifest.json'))
                    self.assertEqual(json.load(archive.extractfile('collection/attempts.json')),records)
                self.assertEqual(len(manifest['segments']),2)
                for segment in manifest['segments']:
                    data=b''
                    for chunk in segment['chunks']:
                        payload=(base/chunk['file_name']).read_bytes()
                        self.assertEqual(hashlib.sha256(payload).hexdigest(),chunk['sha256'])
                        self.assertLessEqual(len(payload),100)
                        data+=payload
                    self.assertEqual(hashlib.sha256(data).hexdigest(),segment['archive_sha256'])
                    path=base/'recovered.tar.gz'; path.write_bytes(data)
                    with tarfile.open(path) as archive:
                        self.assertTrue(any(m.name.endswith('/private.log') for m in archive.getmembers()))
                uploads_before=len(calls)
                saving.save_checkpoint(root,base/'index.tar.gz',records,upload,None)
                self.assertEqual(len(calls),uploads_before+1) # only index, no duplicate parts
            finally:
                saving.CHUNK_BYTES=old

if __name__=='__main__': unittest.main()
