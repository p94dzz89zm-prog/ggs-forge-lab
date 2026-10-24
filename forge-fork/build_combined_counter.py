#!/usr/bin/env python3
"""Overlay only the combined counter-rescue correction on the cycle7 candidate."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE='2f877ea7d5f4cada703c418f0e1a8de7b14592ed4801526f6e4d846b74fd0137'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if sha(base)!=BASE:p.error('Expected verified cycle7 protection candidate')
 if out.exists():p.error('Preserve completed builds; choose a fresh output')
 source=ROOT/'pilot-src/forge/ai/ggs/GgsCounterRescuePolicy.java';name='forge/ai/ggs/GgsCounterRescuePolicy.class';out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',tmp,str(source)],check=True)
  files=[f for f in pathlib.Path(tmp).rglob('*.class')];assert len(files)==1 and files[0].relative_to(tmp).as_posix()==name
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as t:
   for i in z.infolist():t.writestr(i,files[0].read_bytes() if i.filename==name else z.read(i.filename))
 with zipfile.ZipFile(base) as z,zipfile.ZipFile(out) as t:
  assert t.testzip() is None
  assert set(t.namelist())==set(z.namelist())
  assert all(z.read(n)==t.read(n) for n in z.namelist() if n!=name)
 out.with_suffix('.build.json').write_text(json.dumps({'base_sha256':BASE,'candidate_sha256':sha(out),'changed_classes':[name],'source_sha256':sha(source),'other_entries_byte_identical':True,'promotion':False},indent=2)+'\n')
if __name__=='__main__':main()
