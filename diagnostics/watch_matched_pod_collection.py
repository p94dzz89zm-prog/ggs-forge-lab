"""Save recoverable checkpoints and final deliverables for a long pod collection."""
import argparse, io, json, subprocess, tarfile, time
from pathlib import Path
from analyze_matched_pod_collection import analyze, report

def archive_checkpoint(root, destination, records):
    with tarfile.open(destination, 'w:gz', compresslevel=1) as archive:
        archive.add(root/'protocol.json', arcname=root.name+'/protocol.json')
        payload=(json.dumps(records,indent=2)+'\n').encode()
        member=tarfile.TarInfo(root.name+'/attempts.json');member.size=len(payload)
        archive.addfile(member,io.BytesIO(payload))
        for record in records:
            archive.add(root/record['folder'],arcname=root.name+'/'+record['folder'])
        for name in ('finished.json','selected.json'):
            if (root/name).exists():
                archive.add(root/name,arcname=root.name+'/'+name)
    with tarfile.open(destination,'r:gz') as archive:
        saved=json.load(archive.extractfile(root.name+'/attempts.json'))
        assert saved==records
        assert sum(m.name.endswith('/summary.json') for m in archive.getmembers())==len(records)

def upload(helper, uploads):
    process=subprocess.run(['python3',str(helper)],input=json.dumps({'uploads':uploads}),
        text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(process.stdout,flush=True)
    if process.returncode:
        raise RuntimeError('Saving failed; do not blindly retry an uncertain write')
    result=json.loads(process.stdout.strip().splitlines()[-1])
    assert all(r['status']=='succeeded' and r.get('local_metadata_applied') for r in result['results'])
    return result['results']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path);parser.add_argument('--upload-helper',type=Path,required=True)
    parser.add_argument('--checkpoint-every',type=int,default=20)
    args=parser.parse_args();root=args.root.resolve();saved_count=0;identity=None;started=time.monotonic()
    checkpoint=root.parent/'GGS_100_Game_Pod_Data_v17_Checkpoint.tar.gz'
    receipt=root/'checkpoint-save.json'
    if receipt.exists():
        previous=json.loads(receipt.read_text());identity=previous['result'];saved_count=previous['attempts']
    while not (root/'finished.json').exists():
        if time.monotonic()-started>6*3600:
            raise TimeoutError('Collection did not finish within six hours; completed checkpoints retained')
        records=json.loads((root/'attempts.json').read_text()) if (root/'attempts.json').exists() else []
        if len(records)>=saved_count+args.checkpoint_every:
            archive_checkpoint(root,checkpoint,records)
            request={'local_path':str(checkpoint),'purpose':'create_library_file','library_artifact_type':'other'}
            if identity:
                request={'local_path':str(checkpoint),'purpose':'replace_library_file',
                    'library_file_id':identity['library_file_id'],
                    'expected_current_version':identity['current_version_number'],
                    'version_reason':f'{len(records)} attempts checkpointed'}
            print('Saving files to Library',flush=True)
            identity=upload(args.upload_helper,[request])[0];saved_count=len(records)
            receipt.write_text(json.dumps({'attempts':saved_count,'result':identity},indent=2)+'\n')
        time.sleep(20)
    public,comparison=analyze(root)
    public_folder=root/'public-results';public_folder.mkdir(exist_ok=True)
    (public_folder/'analysis.json').write_text(json.dumps(public,indent=2)+'\n')
    (public_folder/'comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
    markdown=root.parent/'GGS_100_Game_Comparison_v17.md';markdown.write_text(report(comparison))
    differential=root.parent/'GGS_100_Game_Differential_v17.json'
    differential.write_text(json.dumps(comparison,indent=2)+'\n')
    final_archive=root.parent/'GGS_100_Per_Deck_Pod_Data_v17.tar.gz'
    records=json.loads((root/'attempts.json').read_text())
    archive_checkpoint(root,final_archive,records)
    print('Saving files to Library',flush=True)
    results=upload(args.upload_helper,[
        {'local_path':str(markdown),'purpose':'create_library_file','library_artifact_type':'report'},
        {'local_path':str(differential),'purpose':'create_library_file','library_artifact_type':'other'},
        {'local_path':str(final_archive),'purpose':'create_library_file','library_artifact_type':'other'}])
    (root/'final-save.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'saved':True,'comparison':comparison}),flush=True)

if __name__=='__main__':
    main()
