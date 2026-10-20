"""Patch only the reviewed controller entry point and narrow Kaito guard."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_SHA256='cd3aa08345b4c3127732d8070c2ffc7064889617464aac1735cede0732ade47d'
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE_SHA256:p.error('Expected the verified Student-corrected base; retain previous combined-lethal correction')
 sources=[ROOT/'pilot-src/forge/ai/AiController.java',ROOT/'pilot-src/forge/ai/ggs/GgsKaitoThreatPolicy.java']
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td);subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
  classes={f.relative_to(root).as_posix():f.read_bytes() for f in root.rglob('*.class')}
  assert sorted(classes)==['forge/ai/AiController$1.class','forge/ai/AiController.class','forge/ai/ggs/GgsKaitoThreatPolicy.class']
  staging=a.output.with_suffix(a.output.suffix+'.building')
  if staging.exists():raise FileExistsError(staging)
  with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED) as new:
   for item in old.infolist():
    if item.filename not in classes:new.writestr(item,old.read(item.filename))
   for name,data in classes.items():new.writestr(name,data)
  with staging.open('rb') as f:os.fsync(f.fileno())
  with zipfile.ZipFile(staging) as z:assert z.testzip() is None
  candidate_hash=hashlib.sha256(staging.read_bytes()).hexdigest()
  assert hashlib.sha256(a.base.read_bytes()).hexdigest()==BASE_SHA256
  os.replace(staging,a.output)
  assert hashlib.sha256(a.output.read_bytes()).hexdigest()==candidate_hash
  print(json.dumps({'base_sha256':hashlib.sha256(a.base.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'changed_classes':sorted(classes),'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}},indent=2))
if __name__=='__main__':main()
