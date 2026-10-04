import hashlib, json, tarfile, tempfile, unittest
from pathlib import Path
import multipart_pod_save as saving

class MultipartRecoveryTest(unittest.TestCase):
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
