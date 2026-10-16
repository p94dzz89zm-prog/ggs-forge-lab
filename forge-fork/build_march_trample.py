#!/usr/bin/env python3
"""Overlay ordinary blocked-trample March planning on a pinned recovered base."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_SHA256='3ced2783c575d8a36c86712b742c84bcab453f31f13be2974a898b2a25dbc1ce'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:p.error('Expected recovered, payment-verified counter-rescue base')
 if out.exists():p.error('Choose a new output; preserve earlier attempts')
 source=ROOT/'baseline-src/forge-ai/src/main/java/forge/ai/ggs/FireworkPilotPolicy.java';out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',tmp,str(source)],check=True)
  changes={f.relative_to(tmp).as_posix():f.read_bytes() for f in pathlib.Path(tmp).rglob('*.class')};names=sorted(changes)
  if names!=['forge/ai/ggs/FireworkPilotPolicy.class']:raise ValueError('Unexpected overlay classes')
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
   for info in z.infolist():target.writestr(info,changes.pop(info.filename,z.read(info.filename)))
  if changes or zipfile.ZipFile(out).testzip() is not None:raise ValueError('Invalid overlay')
 manifest={'base_sha256':BASE_SHA256,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_classes':names,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
 out.with_suffix('.build.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
if __name__=='__main__':main()
