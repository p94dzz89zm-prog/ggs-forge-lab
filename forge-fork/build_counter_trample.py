#!/usr/bin/env python3
"""Add ordinary blocked-trample counter rescue to the verified cycle9 build."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE='a2e98192a6d0a687d4f1d9d732ae1cb78d8c2061e933741aef1eecafe1a76a83'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if sha(base)!=BASE:p.error('Expected the verified cycle9 counter-family build')
 if out.exists():p.error('Preserve prior attempts; choose a fresh output')
 source=ROOT/'pilot-src/forge/ai/ggs/GgsCounterRescuePolicy.java';name='forge/ai/ggs/GgsCounterRescuePolicy.class';out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
  root=pathlib.Path(tmp);subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',str(root),str(source)],check=True)
  files=list(root.rglob('*.class'));assert len(files)==1 and files[0].relative_to(root).as_posix()==name
  candidate=root/'candidate.jar'
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as target:
   for info in z.infolist():target.writestr(info,files[0].read_bytes() if info.filename==name else z.read(info.filename))
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(candidate) as target:
   assert target.testzip() is None and set(z.namelist())==set(target.namelist())
   assert all(z.read(n)==target.read(n) for n in z.namelist() if n!=name)
  os.replace(candidate,out)
 out.with_suffix('.build.json').write_text(json.dumps({'base_sha256':BASE,'candidate_sha256':sha(out),'source_sha256':sha(source),'changed_classes':[name],'other_entries_byte_identical':True,'promotion':False},indent=2)+'\n')
if __name__=='__main__':main()
