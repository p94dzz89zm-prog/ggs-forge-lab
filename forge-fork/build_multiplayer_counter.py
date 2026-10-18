"""Immutable experimental four-player overlay; v1 source/model stay intact."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE='1cf074a29ec72ddf6052cc70a8d17f93ea8b24702943c4924078c0a407cb7c51'
def main():
 p=argparse.ArgumentParser();p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 if a.output.exists():raise FileExistsError(a.output)
 if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Expected frozen cycle20 executable')
 sources=[ROOT/n for n in ['pilot-src/forge/ai/AiController.java','planner-src/forge/ai/simulation/GameCopier.java','pilot-src/forge/ai/ggs/GgsMultiplayerCounterFeatures.java','pilot-src/forge/ai/ggs/GgsMultiplayerCounterPreference.java']]
 with tempfile.TemporaryDirectory() as td:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
  classes={p.relative_to(td).as_posix():p.read_bytes() for p in pathlib.Path(td).rglob('*.class')}
  expected={'forge/ai/AiController.class','forge/ai/AiController$1.class','forge/ai/simulation/GameCopier.class','forge/ai/simulation/GameCopier$CopiedGameObjectMap.class','forge/ai/ggs/GgsMultiplayerCounterFeatures.class','forge/ai/ggs/GgsMultiplayerCounterPreference.class'}
  if set(classes)!=expected:raise ValueError('Unexpected overlay classes: '+str(sorted(classes)))
  staging=a.output.with_suffix('.building')
  with staging.open('xb') as handle:
   with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(handle,'w',zipfile.ZIP_DEFLATED) as new:
    for item in old.infolist():
     if item.filename not in classes:new.writestr(item,old.read(item.filename))
    for n,data in classes.items():new.writestr(n,data)
   handle.flush();os.fsync(handle.fileno())
  with zipfile.ZipFile(staging) as z:assert z.testzip() is None
  if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Base changed during build')
  os.link(staging,a.output);staging.unlink()
  print(json.dumps({'base_sha256':BASE,'jar_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'classes':sorted(classes),'source_sha256':{str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in sources}},indent=2))
if __name__=='__main__':main()
