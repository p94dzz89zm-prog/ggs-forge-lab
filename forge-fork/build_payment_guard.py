"""Exact-base native Pilot A stale-payment guard; no rules-engine replacement."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE = '2ebc317c089a45748a76eb7910372e558a8f46794a9cd196bd936796a644d856'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest() != BASE:
        raise ValueError('Exact verified stack-repair executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:
        raise ValueError('Fresh isolated output required')
    source = Path(__file__).resolve().parent/'pilot-src/forge/ai/validation/RulesValidationController.java'
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base.resolve()),'-d',td,str(source)], check=True)
        changes = {f.relative_to(td).as_posix():f.read_bytes() for f in Path(td).rglob('*.class')}
        if set(changes) != {'forge/ai/validation/RulesValidationController.class'}:
            raise ValueError('Unexpected controller class inventory')
        with zipfile.ZipFile(a.base) as old, zipfile.ZipFile(a.output,'x') as new:
            for info in old.infolist():
                new.writestr(info, changes.get(info.filename,old.read(info.filename)))
        with zipfile.ZipFile(a.base) as old, zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n)==new.read(n) for n in old.namelist() if n not in changes)
        report = dict(base_sha256=BASE, sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
            changed_classes={n:hashlib.sha256(b).hexdigest() for n,b in changes.items()},
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            other_entries_byte_identical=True, full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))

if __name__ == '__main__':main()
