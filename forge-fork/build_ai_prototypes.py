"""Isolate AI-only token prototype IDs over the exact saved diagnostic engine."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent
BASE='452ac5e49c3e839eafb3b6757ad9e8e8ace0ec9edef24c1393b98ccffe809c57'
EXPORT='--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if digest(args.base)!=BASE:raise ValueError('Exact allocation-trace engine required')
    if args.output.exists() or Path('/workspace') in args.output.resolve().parents:
        raise ValueError('Fresh output outside synchronized workspace required')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    sources=[ROOT/'AiPrototypeInstrumenter.java',ROOT/'pilot-src/forge/ai/bridge/AiTokenPrototypes.java']
    with tempfile.TemporaryDirectory(dir=args.output.parent) as temporary:
        root=Path(temporary);classes=root/'classes';classes.mkdir()
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main',EXPORT,'-cp',str(args.base),'-d',str(classes),*[str(p) for p in sources]],check=True)
        names=['forge/ai/ability/TokenAi.class','forge/game/card/token/TokenInfo.class','forge/game/Game.class']
        with zipfile.ZipFile(args.base) as archive:
            for name in names:
                path=root/'input'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(name))
        subprocess.run(['java',EXPORT,'-cp',str(classes)+':'+str(args.base),'AiPrototypeInstrumenter',str(root/'input'),str(root/'output')],check=True)
        changes={name:(root/'output'/name).read_bytes() for name in names}
        helper='forge/ai/bridge/AiTokenPrototypes.class'
        with zipfile.ZipFile(args.base) as old,zipfile.ZipFile(args.output,'x',zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():new.writestr(entry,changes.get(entry.filename,old.read(entry.filename)))
            new.writestr(helper,(classes/helper).read_bytes())
    report=dict(base_sha256=BASE,sha256=digest(args.output),scope='Only TokenAi preview factory IDs; real token path retains native allocator',historical_identity_mapping=False,full_game_approved=False,source_sha256={str(p.relative_to(ROOT)):digest(p) for p in sources})
    args.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
