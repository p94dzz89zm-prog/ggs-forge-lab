"""Exact-base action outcome and private transaction-evidence overlay."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE='093c2bbb6cc7d744e689737de993b76f34072a6066a59225f7c554861ffeb0dd'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--java',default='java');a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact house executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    root=Path(__file__).resolve().parent;a.output.parent.mkdir(parents=True,exist_ok=True)
    sources=[root/'pilot-src/forge/ai/bridge/EngineEvidence.java',root/'pilot-src/forge/ai/validation/RulesValidationController.java']
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        subprocess.run([a.java,'-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
        changes={x.relative_to(td).as_posix():x.read_bytes() for x in Path(td).rglob('*.class')}
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            if not set(changes)<=set(old.namelist()):raise ValueError('Unexpected new evidence class')
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info.filename)))
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
            changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},
            source_sha256={s.relative_to(root).as_posix():hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
            other_entries_byte_identical=True,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
