"""Default-off causal identity overlay over the exact stage36 engine."""
import argparse,json,subprocess,tempfile,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from executable_delta import digest,publish
ROOT=Path(__file__).resolve().parent
BASES={'748a6d2d3c66f847402d43a0ea09e24e081f07c8ebdc078742104fb819f0c5f8',
       '8335712a7f805cfba996611988ce039870222f4ef3a6a6cb6086e2eb9f5771d6',
       '81dfab791e69ac76efd44010a2220ac51c3890e2eabdbdde96f471a4a6170b81',
       '16e8bcb9abc037a2ac2601fa35a5c026a988b152ca6272b5b64979938eb09563',
       '8a2f0149d266ea1407b221c1a1c874d581c9367af768ee4501e72da9465496ec',
       '22b04e01aebdc51fef4e19dee328bb50cecde063fbf0650e50307c0c5b5b79e0',
       '0b47f08f481ecea1caf66abbc206d27ec1e8c0a69f101e03a71a6a75e85cf055',
       '63e111769dcd5f12e8ba5c480efb0c5c0252427cd9c42134de89014299aa64aa'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    base=digest(a.base)
    if base not in BASES:raise ValueError('Exact saved stage36–42 executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh nonsynchronized output required')
    sources=[ROOT/'pilot-src/forge/ai/bridge'/name for name in ('ReplayCardIdentities.java','EngineEvidence.java','DecisionReplay.java')]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as temp:
        root=Path(temp);classes=root/'classes';classes.mkdir()
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-cp',str(a.base),'-d',str(classes),*map(str,sources)],check=True)
        changes={file.relative_to(classes).as_posix():file.read_bytes() for file in classes.rglob('*.class')}
        staged=root/'engine.jar'
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(staged,'w',zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():new.writestr(entry,changes.get(entry.filename,old.read(entry.filename)))
            for name,data in sorted(changes.items()):
                if name not in old.namelist():new.writestr(name,data)
        publish(staged,a.output)
    report=dict(base_sha256=base,sha256=digest(a.output),source_sha256={str(source.relative_to(ROOT)):digest(source) for source in sources},default_enabled=False,rules_approved=False)
    a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
