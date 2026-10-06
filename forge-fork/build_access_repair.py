#!/usr/bin/env python3
"""Build the access/Frostcliff repair over the exact audited v24 executable."""
import argparse, hashlib, json, pathlib, subprocess, tempfile, zipfile

BASE_SHA256 = '7c48b167f44b6bcf4cdc3472425346a0cad3deb2fcddaeb5e4029465201e1e60'
ROOT = pathlib.Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=pathlib.Path,required=True)
    p.add_argument('--output',type=pathlib.Path,required=True)
    a=p.parse_args();base=a.base.resolve();output=a.output.resolve()
    if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:
        p.error('Base executable differs from the audited v24 build')
    if output.exists():p.error('Choose a new output file')
    sources=sorted((ROOT/'access-src').rglob('*.java'))
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['java','-XX:-UsePerfData','-m','jdk.compiler/com.sun.tools.javac.Main',
            '-cp',str(base),'-d',tmp,*map(str,sources)],check=True)
        classes={f.relative_to(tmp).as_posix():f.read_bytes() for f in pathlib.Path(tmp).rglob('*.class')}
        replaced=sorted(classes)
        with zipfile.ZipFile(base) as source,zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as target:
            for info in source.infolist():
                target.writestr(info,classes.pop(info.filename,source.read(info.filename)))
            for name,data in sorted(classes.items()):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                target.writestr(info,data)
    manifest={'base_sha256':BASE_SHA256,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'sources':{f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
        'replaced_classes':replaced}
    output.with_suffix('.build.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
