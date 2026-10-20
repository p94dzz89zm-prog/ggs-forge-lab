"""Exact-base evidence-writer optimization; verify all other entries unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE='c0feb854feb03ef74e18297b784acda43f4bcee15ebc063e14c9f5c007cca607'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact native-validation base required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    root=Path(__file__).resolve().parent
    sources=[root/'pilot-src/forge/ai/bridge'/n for n in ('DurableEvidence.java','EngineEvidence.java')]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work=Path(td)
        subprocess.run([a.java,'-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
        changes={p.relative_to(work).as_posix():p.read_bytes() for p in work.rglob('*.class')}
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            if not set(changes)<=set(old.namelist()):raise ValueError('Unexpected new writer class')
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        result=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
            changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},
            source_sha256={s.relative_to(root).as_posix():hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
            other_entries_byte_identical=True,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
