"""Expose the existing Forge AI decision clock without changing rules or heuristics."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE='43b8dded3ad4316c12632cd0ed359f687b79c461da3b8a68e365481d5f15dcfb'
ENTRY='forge/view/SimulateMatch.class'
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert hashlib.sha256(a.base.read_bytes()).hexdigest()==BASE
assert not a.output.exists()
source=ROOT/'forge-fork/access-src/forge/view/SimulateMatch.java';text=source.read_text();needle='        g1.setNoGUIUser();';assert text.count(needle)==1
patch=needle+'\n        g1.AI_TIMEOUT = Integer.getInteger("dragonmind.aiDecisionTimeoutSeconds", 5);\n        if (g1.AI_TIMEOUT < 1) throw new IllegalArgumentException("AI decision timeout must be positive");'
with tempfile.TemporaryDirectory() as d:
 tmp=Path(d)
 def compile_source(name,value):
  src=tmp/name/'src/forge/view/SimulateMatch.java';src.parent.mkdir(parents=True);src.write_text(value);out=tmp/name/'classes';out.mkdir()
  subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',str(out),str(src)],check=True)
  files=list(out.rglob('*.class'));assert len(files)==1 and files[0].relative_to(out).as_posix()==ENTRY
  return files[0].read_bytes()
 original=compile_source('original',text);changed=compile_source('clock',text.replace(needle,patch))
 with zipfile.ZipFile(a.base) as src:
  assert original==src.read(ENTRY),'Source does not exactly reproduce audited entrypoint'
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as dst:
   for info in src.infolist():dst.writestr(info,changed if info.filename==ENTRY else src.read(info.filename))
 with zipfile.ZipFile(a.base) as src,zipfile.ZipFile(a.output) as dst:
  assert src.namelist()==dst.namelist()
  differences=[n for n in src.namelist() if src.read(n)!=dst.read(n)];assert differences==[ENTRY]
receipt={'base_sha256':BASE,'patched_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'original_source_recompiled_byte_exact':True,'changed_class':ENTRY,'change':'Expose existing Game.AI_TIMEOUT as explicit JVM decision-clock property; default remains5.'}
a.output.with_suffix('.build.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
