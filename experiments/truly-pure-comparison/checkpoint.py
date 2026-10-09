"""Completed-game evidence only; atomic archive, full member/footer validation."""
import argparse,gzip,hashlib,json,subprocess,tarfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT.parent
p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);a=p.parse_args();batch=a.batch.resolve();rows=json.loads((batch/'summary.json').read_text());rows=[r for r in rows if r['status']=='completed']
out=WORK/'truly-pure-comparison/checkpoints';out.mkdir(parents=True,exist_ok=True);saved=set()
for r in out.glob('*-receipt.json'):
 receipt=json.loads(r.read_text())
 if receipt.get('saved'):saved.update(receipt['keys'])
key=lambda r:f"{batch.name}/{r['variant']}/{r['seed']}/r{r['seat_rotation']}"
new=[r for r in rows if key(r) not in saved]
if not new:print('No new completed games');raise SystemExit(0)
number=max([int(p.name.split('-')[1]) for p in out.glob('part-*-receipt.json')]+[0])+1
archive=out/f'Truly_Pure_Comparison_Evidence_Part_{number:03}.tar.gz';paths=set()
for r in new:
 label=Path(r['log']).stem;k=f"{r['variant']}-{r['seed']}-r{r['seat_rotation']}"
 paths.update([batch/r['log'],batch/r['engine_transcript'],batch/r['engine_record']]);paths.update((batch/'audit'/label).glob('*.jsonl.gz'));paths.update((batch/'analysis').glob(k+'*'))
paths.update([ROOT/'experiments/truly-pure-comparison/protocol.json',WORK/'comparison-validation/legal-import-private.log',batch/'metadata.json'])
manifest={'keys':[key(r) for r in new],'rows':new,'files':{str(p.relative_to(WORK)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}}
mp=out/f'part-{number:03}-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');paths.add(mp)
temporary=archive.with_suffix('.tmp')
with tarfile.open(temporary,'w:gz',compresslevel=4) as tar:
 for path in sorted(paths):tar.add(path,arcname=str(path.relative_to(WORK)),recursive=False)
with gzip.open(temporary,'rb') as f:
 while f.read(1<<20):pass
with tarfile.open(temporary,'r:gz') as tar:
 for m in tar:
  with tar.extractfile(m) as f:
   h=hashlib.sha256()
   while b:=f.read(1<<20):h.update(b)
  if m.name in manifest['files']:assert h.hexdigest()==manifest['files'][m.name]
temporary.replace(archive)
request={'uploads':[{'local_path':str(archive),'purpose':'create_library_file','directory_id':'6a8249fab85c8191a7fcb8390fc88fc5','library_artifact_type':'other'}]}
run=subprocess.run(['python3',str(WORK/'comparison-recovery/helpers/library_upload.py')],input=json.dumps(request),text=True,capture_output=True)
if run.returncode:raise RuntimeError('Evidence save failed: '+run.stderr[-300:])
response=json.loads(run.stdout);assert len(response['results'])==1 and response['results'][0]['status']=='succeeded',response
sys.path.insert(0,str(WORK/'comparison-recovery/helpers'));from library_hosted_apps import HostedAppsClient
verified=out/'verified';verified.mkdir(exist_ok=True);lid=response['results'][0]['library_file_id'];reply=HostedAppsClient().call_tool('connector_openai_library','prepare_materialize',{'items':[{'library_file_id':lid}],'destination':{'directory':str(verified)}})
content=reply['structuredContent'];transfers=content.get('result',content)['transfers'];assert len(transfers)==1;t=transfers[0]
helper=WORK/'comparison-recovery/helpers/library_file_transfer.py'
if t.get('workspace_path'):
 remote=Path(t['workspace_path']);subprocess.run(['python3',str(helper),'apply-xattrs',str(remote),lid],input=json.dumps(t.get('xattrs',[])),text=True,check=True,capture_output=True)
else:
 remote=verified/archive.name;subprocess.run(['python3',str(helper),'materialize',str(remote)],input=json.dumps(t),text=True,check=True,capture_output=True)
assert hashlib.sha256(remote.read_bytes()).digest()==hashlib.sha256(archive.read_bytes()).digest()
with gzip.open(remote,'rb') as f:
 while f.read(1<<20):pass
receipt={'saved':True,'materialized_byte_identical':True,'full_gzip_footer_verified':True,'keys':manifest['keys'],'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'response':response}
(out/f'part-{number:03}-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'saved_games':len(new),'part':number,'bytes':receipt['bytes'],'library_file_id':response['results'][0]['library_file_id']}))
