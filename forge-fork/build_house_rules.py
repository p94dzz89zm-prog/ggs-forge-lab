"""Reproducible explicit Commander house variant over the verified keyword build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE='9265d587f40a4a0d0c4f711d66ecdb7dd9bfbf5696ccacf3ca1805d22a839a43'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact keyword executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    root=Path(__file__).resolve().parent;a.output.parent.mkdir(parents=True,exist_ok=True)
    sources=[root/'HouseRulesInstrumenter.java',*(root/'pilot-src/forge/game/mulligan').glob('*.java')]
    exports=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED']
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work=Path(td)
        subprocess.run([a.java,*exports,'-m','jdk.compiler/com.sun.tools.javac.Main',*exports,'-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
        changes={x.relative_to(work).as_posix():x.read_bytes() for x in (work/'forge').rglob('*.class')}
        for name in ['forge/game/player/RegisteredPlayer.class','forge/game/player/Player.class','forge/game/mulligan/MulliganService.class']:
            before=work/'original.class';after=work/'patched.class'
            with zipfile.ZipFile(a.base) as old:before.write_bytes(old.read(name))
            subprocess.run([a.java,*exports,'-cp',td+os.pathsep+str(a.base.resolve()),'HouseRulesInstrumenter',str(before),str(after)],check=True)
            changes[name]=after.read_bytes();after.unlink()
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
            for name in sorted(set(changes)-set(old.namelist())):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;new.writestr(info,changes[name])
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
                    changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},
                    source_sha256={s.relative_to(root).as_posix():hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
                    other_entries_byte_identical=True,profile='ggs-house-v1',default_enabled=False,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
