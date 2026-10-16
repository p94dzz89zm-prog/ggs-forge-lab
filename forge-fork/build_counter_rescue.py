#!/usr/bin/env python3
"""Overlay a narrow counter-rescue guard on the pinned March-corrected engine."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_SHA256='8f00134d9512e1552d9b09b85dfce349720c88fc66a548cf079ecc608729dd01'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:p.error('Expected verified March-corrected executable')
 if out.exists():p.error('Choose a new output; preserve previous attempts')
 sources=[ROOT/'pilot-src/forge/ai/AiController.java',ROOT/'pilot-src/forge/ai/ggs/GgsCounterRescuePolicy.java']
 out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',tmp,*map(str,sources)],check=True)
  changes={f.relative_to(tmp).as_posix():f.read_bytes() for f in pathlib.Path(tmp).rglob('*.class')};names=sorted(changes)
  if names!=['forge/ai/AiController$1.class','forge/ai/AiController.class','forge/ai/ggs/GgsCounterRescuePolicy.class']:raise ValueError('Unexpected overlay classes')
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
   for info in z.infolist():target.writestr(info,changes.pop(info.filename,z.read(info.filename)))
   for name,data in changes.items():target.writestr(name,data)
  if zipfile.ZipFile(out).testzip() is not None:raise ValueError('Invalid overlay ZIP')
 manifest={'base_sha256':BASE_SHA256,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'overlay_classes':names,'source_sha256':{f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}}
 out.with_suffix('.build.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
if __name__=='__main__':main()
