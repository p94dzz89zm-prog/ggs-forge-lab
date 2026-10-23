"""Build an isolated mulligan-round overlay without replacing policy hooks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--expected-base-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--java', default='java')
    a = p.parse_args()
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if digest(a.base) != a.expected_base_sha256:
        raise ValueError('Base hash differs from recorded allocation')
    if a.output.exists() or a.output.with_suffix('.build.json').exists():
        raise ValueError('Fresh output required')
    root = Path(__file__).resolve().parent
    sources = [root/'MulliganRoundInstrumenter.java', root/'pilot-src/forge/game/mulligan/MulliganRoundProtocol.java']
    exports = ['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED',
               '--add-exports=java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED']
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work = Path(td)
        subprocess.run([a.java, *exports, '-m', 'jdk.compiler/com.sun.tools.javac.Main', *exports,
                        '-cp', str(a.base.resolve()), '-d', td, *map(str, sources)], check=True)
        name = 'forge/game/mulligan/MulliganService.class'
        with zipfile.ZipFile(a.base) as old:
            (work/'before.class').write_bytes(old.read(name))
        subprocess.run([a.java, *exports, '-cp', td + os.pathsep + str(a.base.resolve()),
                        'MulliganRoundInstrumenter', str(work/'before.class'), str(work/'after.class')], check=True)
        changes = {name: (work/'after.class').read_bytes(),
                   'forge/game/mulligan/MulliganRoundProtocol.class': (work/'forge/game/mulligan/MulliganRoundProtocol.class').read_bytes()}
        with zipfile.ZipFile(a.base) as old:
            if set(changes) - {name} & set(old.namelist()):
                raise ValueError('Overlay already present')
            with zipfile.ZipFile(a.output, 'x') as new:
                for info in old.infolist(): new.writestr(info, changes.get(info.filename, old.read(info)))
                for key in sorted(set(changes) - set(old.namelist())):
                    info = zipfile.ZipInfo(key, (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                    new.writestr(info, changes[key])
        with zipfile.ZipFile(a.base) as old, zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None
            assert all(old.read(n) == new.read(n) for n in old.namelist() if n not in changes)
        report = dict(base_sha256=a.expected_base_sha256, output_sha256=digest(a.output),
                      source_sha256={s.relative_to(root).as_posix(): digest(s) for s in sources},
                      changed_classes={n: hashlib.sha256(b).hexdigest() for n, b in changes.items()},
                      other_entries_byte_identical=True, other_service_methods_preserved=True,
                      scope='round declaration ordering only; existing mulligan policy unchanged',
                      full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))


if __name__ == '__main__':
    main()
