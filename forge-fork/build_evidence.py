"""Evidence-only overlay on the frozen Cycle22 executable; no policy changes."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE='ceb4e12f20919c3b46f04bc620ea0f5cdb005745ab855b6c08bd2ccc696c5709'
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Frozen Cycle22 executable required')
 if a.output.exists():raise FileExistsError(a.output)
 sources=[ROOT/'pilot-src/forge/ai/bridge'/n for n in ['BridgeSnapshot.java','BridgeAudit.java','PlayerControllerBridge.java','DurableEvidence.java']]+[ROOT/'access-src/forge/view/SimulateMatch.java']
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
  root=pathlib.Path(td);subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',str(root),*map(str,sources)],check=True)
  classes={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*.class')}
  staged=root/'evidence.jar'
  with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED) as new:
   for info in old.infolist():new.writestr(info,classes.get(info.filename,old.read(info.filename)))
   for n,data in sorted(classes.items()):
    if n not in old.namelist():new.writestr(n,data)
  with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(staged) as new:
   assert new.testzip() is None
   assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in classes)
  with staged.open('rb') as f:os.fsync(f.fileno())
  os.link(staged,a.output)
  fd=os.open(a.output.parent,os.O_DIRECTORY)
  try:os.fsync(fd)
  finally:os.close(fd)
  manifest={'base_sha256':BASE,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'classes':sorted(classes),'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},'other_entries_byte_identical':True,'promotion':False}
  a.output.with_suffix('.build.json').write_text(json.dumps(manifest,indent=2)+'\n')
  print(json.dumps(manifest))
if __name__=='__main__':main()
