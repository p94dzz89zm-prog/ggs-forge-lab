"""Build the explicit casual-seven overlay; never replace the frozen experiment executable."""
import argparse,hashlib,subprocess,tempfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
expected='d9278b1ddd644ef6dd458b19cfabee20d3c2e9fde51d1cf10827a91c842616ee'
assert hashlib.sha256(a.base.read_bytes()).hexdigest()==expected,'Not the frozen v28 base'
assert not a.output.exists(),'Refuse to replace an existing executable'
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)
 subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',str(out),*[str(x) for x in sorted((here/'src').rglob('*.java'))]],check=True)
 replacements={str(x.relative_to(out)):x.read_bytes() for x in out.rglob('*.class')}
 assert set(replacements)=={'forge/game/mulligan/MulliganService.class','forge/game/mulligan/MulliganService$1.class','forge/game/mulligan/CasualSeven.class'}
 with zipfile.ZipFile(a.base) as base,zipfile.ZipFile(a.output,'w') as dest:
  for info in base.infolist():dest.writestr(info,replacements.pop(info.filename,base.read(info.filename)))
  for name,content in replacements.items():
   info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;dest.writestr(info,content)
print(hashlib.sha256(a.output.read_bytes()).hexdigest(),a.output)
