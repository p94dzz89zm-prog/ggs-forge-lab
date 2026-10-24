"""Build opt-in validation controller over exact preserved readiness executable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE='e9d2f5802c5d6c690f99fe4be423d57546a71161d6ac7b107479dca68d5cbeb2'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact readiness executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    a.output.parent.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parent
    sources=[root/'ValidationPilotInstrumenter.java',root/'pilot-src/forge/ai/validation/RulesValidationController.java']
    exports=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED']
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work=Path(td)
        subprocess.run([a.java,*exports,'-m','jdk.compiler/com.sun.tools.javac.Main',*exports,'-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
        with zipfile.ZipFile(a.base) as z:(work/'original.class').write_bytes(z.read('forge/ai/LobbyPlayerAi.class'))
        subprocess.run([a.java,*exports,'-cp',td+os.pathsep+str(a.base.resolve()),'ValidationPilotInstrumenter',str(work/'original.class'),str(work/'patched.class')],check=True)
        changes={'forge/ai/LobbyPlayerAi.class':(work/'patched.class').read_bytes()}
        changes.update({x.relative_to(work).as_posix():x.read_bytes() for x in (work/'forge').rglob('*.class')})
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
            for name in sorted(set(changes)-set(old.namelist())):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;new.writestr(info,changes[name])
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
            changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},other_entries_byte_identical=True,
            source_sha256={s.relative_to(root).as_posix():hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
            default_enabled=False,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
