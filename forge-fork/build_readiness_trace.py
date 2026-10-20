"""Deterministic evidence-only overlay; never modifies the pinned input JAR."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

BASE = 'b1521760e6448630079102e9917ecd74293300e34ab577140ccc0de67b8e8762'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--java', default='java')
    a = p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest() != BASE:
        raise ValueError('Exact Stage47 base required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:
        raise ValueError('Fresh isolated output outside /workspace required')
    root = Path(__file__).resolve().parent
    sources = [root/'ReadinessInstrumenter.java', root/'pilot-src/forge/ai/bridge/ReadinessTrace.java']
    exports = ['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED',
               '--add-exports=java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED']
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work = Path(td)
        subprocess.run([a.java, *exports, '-m', 'jdk.compiler/com.sun.tools.javac.Main',
                        *exports, '-cp', str(a.base.resolve()), '-d', td,
                        *map(str, sources)], check=True)
        with zipfile.ZipFile(a.base) as z:
            (work/'PhaseHandler.class').write_bytes(z.read('forge/game/phase/PhaseHandler.class'))
        subprocess.run([a.java, *exports, '-cp', td+os.pathsep+str(a.base.resolve()),
                        'ReadinessInstrumenter', str(work/'PhaseHandler.class'), str(work/'PhaseHandler-traced.class')], check=True)
        changes = {'forge/game/phase/PhaseHandler.class': (work/'PhaseHandler-traced.class').read_bytes(),
                   'forge/ai/bridge/ReadinessTrace.class': (work/'forge/ai/bridge/ReadinessTrace.class').read_bytes()}
        with zipfile.ZipFile(a.base) as old, zipfile.ZipFile(a.output, 'x') as new:
            for info in old.infolist():
                new.writestr(info, changes.get(info.filename, old.read(info.filename)))
            for name in sorted(set(changes)-set(old.namelist())):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                new.writestr(info, changes[name])
        with zipfile.ZipFile(a.base) as old, zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n) == new.read(n) for n in old.namelist() if n not in changes)
        manifest = dict(base_sha256=BASE, sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
                        changed_classes={n: hashlib.sha256(b).hexdigest() for n,b in changes.items()},
                        source_sha256={str(s.relative_to(root)): hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},
                        other_entries_byte_identical=True, default_enabled=False, rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(manifest, indent=2)+'\n')
        print(json.dumps(manifest))


if __name__ == '__main__':
    main()
