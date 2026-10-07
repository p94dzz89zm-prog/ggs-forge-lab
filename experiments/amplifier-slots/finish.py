"""Create and persist final deliverables only after the registered collection finishes."""
import hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];WORK=ROOT.parent;OUT=WORK/'amplifier-slots'
assert (OUT/'collection-completed.json').exists(),'Collection is not complete'
r=json.loads((OUT/'Pure_GGS_Amplifier_Results.json').read_text());assert not r['unresolved_exclusions']
assert len(r['arms'])==6 and all(a['valid']>=64 and (a['stability']['passed'] or a['valid']==128) for a in r['arms'])
saved=OUT/'final-deliverables-save.json'
if saved.exists():
 prior=json.loads(saved.read_text())['results']
 if len(prior)==5 and all(x['status']=='succeeded' for x in prior):
  print('Final deliverables already saved; not duplicating them');raise SystemExit(0)
subprocess.run([sys.executable,str(HERE/'report.py')],check=True)
git=lambda ref:subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()
assert not subprocess.run(['git','diff','--quiet'],cwd=ROOT).returncode,'Publish tracked changes before sealing source provenance'
assert git('HEAD^{tree}')==git('FETCH_HEAD^{tree}'),'Published source tree differs from local source'
index={'protocol':r['protocol'],'operational_amendment':json.loads((OUT/'Pure_GGS_Deadline_Amendment.json').read_text()),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'attempted':r['attempted'],'valid':r['valid'],'excluded':r['excluded'],'evidence_files':[],'integrity_receipts':{},'baseline_evidence':{'results':'libfile_c61413031b2c8191abac8622c20051b6','engine_v28':'libfile_eda2e9500280819187bcae0b814b7077','part01':'libfile_c95300f07d1c81919f6dbbdeb582df8a','part02':'libfile_07b9545af1448191aaecca824ed7805b','part03':'libfile_22282b785844819185264d70b8582be4','part04':'libfile_ad554ddbc87c81919d05b9c4468954a2','part05':'libfile_f47130ae7ee8819193ada35c0d6b69af'}}
index['concurrency_amendment']=json.loads((OUT/'Pure_GGS_Concurrency_Amendment.json').read_text())
index['execution_interruptions']=r.get('execution_interruptions');index['known_attempted_total']=r.get('known_attempted_total',r['attempted'])
index['restoration_validation']=json.loads((OUT/'restoration-validation-receipt.json').read_text())
index['source_local_commit']=index['source_commit'];index['source_commit']=git('FETCH_HEAD');index['source_tree_sha']=git('FETCH_HEAD^{tree}')
for f in sorted((OUT/'saved-chunks').glob('*.json'))+[OUT/'audit-repair-save.json',OUT/'timeout-diagnostic-save.json',OUT/'deadline-amendment-save.json',OUT/'late-timeout-evidence-save.json',OUT/'workspace-restoration-save.json']:
 results=json.loads(f.read_text())['results'];assert all(x['status']=='succeeded' for x in results)
 index['evidence_files'].extend({'file_name':x['file_name'],'library_file_id':x['library_file_id'],'receipt':f.name} for x in results)
for d in [OUT/'gate',OUT/'deadline-gate',OUT/'concurrency-gate',*sorted(OUT.glob('stage-*'))]:
 if (d/'audit-integrity.json').exists():index['integrity_receipts'][d.name]=json.loads((d/'audit-integrity.json').read_text())
p=OUT/'Pure_GGS_Amplifier_Evidence_Index.json';p.write_text(json.dumps(index,indent=2)+'\n')
files=[OUT/'Pure_GGS_Amplifier_Report.md',OUT/'Pure_GGS_Amplifier_Per_Game.csv',OUT/'Pure_GGS_Amplifier_Results.json',OUT/'Pure_GGS_Amplifier_Representative_Logs.zip',p]
request={'uploads':[{'local_path':str(p),'purpose':'create_library_file','directory_id':'6a8249fab85c8191a7fcb8390fc88fc5','library_artifact_type':'report' if p.suffix=='.md' else 'other'} for p in files]}
proc=subprocess.run(['python3','/root/.codex/plugins/cache/openai-curated-remote/openai-library/0.1.61/skills/library/scripts/library_upload.py'],input=json.dumps(request),text=True,capture_output=True,cwd=WORK);receipt=OUT/'final-deliverables-save.json';receipt.write_text(proc.stdout);assert not proc.returncode
results=json.loads(proc.stdout)['results'];assert len(results)==len(files) and all(x['status']=='succeeded' for x in results)
print(json.dumps({'attempted':r['attempted'],'valid':r['valid'],'excluded':len(r['excluded']),'saved':[{'file_name':x['file_name'],'library_file_id':x['library_file_id']} for x in results]},indent=2))
