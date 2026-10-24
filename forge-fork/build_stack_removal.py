"""Generic duplicate-notification repair over the exact verified execution build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE='ee284763a8a9983c9a8146ce5bada123d829ea8f7cebd7810788228c4a1f0729'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact execution-evidence executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    root=Path(__file__).resolve().parent;a.output.parent.mkdir(parents=True,exist_ok=True);source=root/'StackRemovalInstrumenter.java'
    exports=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED']
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work=Path(td);subprocess.run([a.java,*exports,'-m','jdk.compiler/com.sun.tools.javac.Main',*exports,'-cp',str(a.base.resolve()),'-d',td,str(source)],check=True)
        name='forge/game/zone/MagicStack.class'
        with zipfile.ZipFile(a.base) as z:(work/'original.class').write_bytes(z.read(name))
        subprocess.run([a.java,*exports,'-cp',td+os.pathsep+str(a.base.resolve()),'StackRemovalInstrumenter',str(work/'original.class'),str(work/'patched.class')],check=True)
        change=(work/'patched.class').read_bytes()
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            for info in old.infolist():new.writestr(info,change if info.filename==name else old.read(info.filename))
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None and all(old.read(n)==new.read(n) for n in old.namelist() if n!=name)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),changed_classes={name:hashlib.sha256(change).hexdigest()},source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),other_entries_byte_identical=True,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
