#!/usr/bin/env python3
"""Replace only the Student forecast policy over the verified cycle12 build."""
import argparse,hashlib,json,os,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE='c577030d4d2e17e6fb4624ba8d1ffce7524631e3e39daef60fc5d9b06b1e25c1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if sha(base)!=BASE:p.error('Expected verified experimental cycle12 executable')
 if out.exists():p.error('Preserve attempts; choose a fresh output')
 source=ROOT/'pilot-src/forge/ai/ggs/GgsNinjutsuPolicy.java';allowed={'forge/ai/ggs/GgsNinjutsuPolicy.class','forge/ai/ggs/GgsNinjutsuPolicy$Plan.class'};out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
  root=pathlib.Path(tmp);subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',str(root),str(source)],check=True)
  classes={f.relative_to(root).as_posix():f.read_bytes() for f in root.rglob('*.class')};assert set(classes)==allowed
  staged=root/'candidate.jar'
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED) as target:
   for info in z.infolist():target.writestr(info,classes.get(info.filename,z.read(info.filename)))
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(staged) as target:
   assert target.testzip() is None and z.namelist()==target.namelist()
   changed=[n for n in z.namelist() if z.read(n)!=target.read(n)];assert set(changed)<=allowed and 'forge/ai/ggs/GgsNinjutsuPolicy.class' in changed
  os.replace(staged,out)
 out.with_suffix('.build.json').write_text(json.dumps({'base_sha256':BASE,'candidate_sha256':sha(out),'source_sha256':sha(source),'changed_classes':changed,'all_other_entries_byte_identical':True,'promotion':False},indent=2)+'\n')
if __name__=='__main__':main()
