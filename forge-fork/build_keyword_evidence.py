"""Typed keyword evidence over the exact preserved structured-writer executable."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE = '4073cae36981ce2bed73a3319376323657c99a167b9fc81198d8a3cfe1cbff25'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact structured-writer executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    root=Path(__file__).resolve().parent
    source=root/'pilot-src/forge/ai/bridge/EngineEvidence.java'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        subprocess.run([a.java,'-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,str(source)],check=True)
        changes={x.relative_to(td).as_posix():x.read_bytes() for x in Path(td).rglob('*.class')}
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            if not set(changes)<=set(old.namelist()):raise ValueError('Unexpected new evidence class')
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
                    changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    other_entries_byte_identical=True,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
