"""Opt-in experimental learned-counter hook over the verified cycle18 engine."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,zipfile,os
ROOT=pathlib.Path(__file__).resolve().parent
BASE='66c1dba5dde1f2b85fbd59d07c114d727fd87347b0b3b07593c166fdece77744'
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Expected preserved cycle18 candidate')
 sources=[ROOT/'pilot-src/forge/ai/AiController.java',ROOT/'pilot-src/forge/ai/ggs/GgsLearnedCounterPreference.java']
 with tempfile.TemporaryDirectory() as td:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
  classes={p.relative_to(td).as_posix():p.read_bytes() for p in pathlib.Path(td).rglob('*.class')}
  assert set(classes)=={'forge/ai/AiController.class','forge/ai/AiController$1.class','forge/ai/ggs/GgsLearnedCounterPreference.class'}
  staging=a.output.with_suffix('.building')
  with staging.open('xb') as handle:
   with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(handle,'w',zipfile.ZIP_DEFLATED) as z:
    for item in old.infolist():
     if item.filename not in classes:z.writestr(item,old.read(item.filename))
    for name,data in classes.items():z.writestr(name,data)
   handle.flush();os.fsync(handle.fileno())
  with zipfile.ZipFile(staging) as z:assert z.testzip() is None
  assert hashlib.sha256(a.base.read_bytes()).hexdigest()==BASE
  os.link(staging,a.output);staging.unlink()
  print(json.dumps({'base_sha256':BASE,'jar_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'classes':sorted(classes)},indent=2))
if __name__=='__main__':main()
