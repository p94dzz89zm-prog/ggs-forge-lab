#!/usr/bin/env python3
"""Overlay the opt-in public-projection planner on the preserved cycle4 engine."""
import argparse,hashlib,json,pathlib,subprocess,tempfile,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
BASE_SHA256='0a2eec734e76dedc101f7bc699efde62b59d5c5952c161b1a216b5ba993f588f'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();base=a.base.resolve();out=a.output.resolve()
 if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:p.error('Expected payment/trample-verified cycle4 incumbent')
 if out.exists():p.error('Choose a new output; preserve earlier attempts')
 sources=sorted((ROOT/'planner-src').rglob('*.java'))+[ROOT/'pilot-src'/name for name in ['forge/ai/ComputerUtil.java','forge/ai/AiController.java','forge/ai/bridge/BridgeAudit.java','forge/ai/bridge/PlayerControllerBridge.java']]
 out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as tmp:
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(base),'-d',tmp,*map(str,sources)],check=True)
  changes={f.relative_to(tmp).as_posix():f.read_bytes() for f in pathlib.Path(tmp).rglob('*.class')}
  allowed=['forge/ai/ComputerUtil','forge/ai/AiController','forge/ai/bridge/BridgeAudit','forge/ai/bridge/PlayerControllerBridge','forge/ai/simulation/GameCopier','forge/ai/ggs/PlannerContext','forge/ai/ggs/PlannerSnapshot','forge/ai/ggs/PlannerTrace','forge/ai/ggs/GgsLinePlanner']
  if any(not any(n==v+'.class' or n.startswith(v+'$') for v in allowed) for n in changes):raise ValueError('Unexpected overlay')
  names=sorted(changes)
  with zipfile.ZipFile(base) as z,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as target:
   for info in z.infolist():target.writestr(info,changes.pop(info.filename,z.read(info.filename)))
   for name,data in changes.items():target.writestr(name,data)
  with zipfile.ZipFile(out) as candidate,zipfile.ZipFile(base) as original:
   if candidate.testzip() is not None:raise ValueError('Invalid ZIP')
   for n in original.namelist():
    if n not in names and candidate.read(n)!=original.read(n):raise ValueError('Unexpected content change '+n)
 manifest={'base_sha256':BASE_SHA256,'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_classes':names,'default_enabled':False,'source_sha256':{str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in sources}}
 out.with_suffix('.build.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
if __name__=='__main__':main()
