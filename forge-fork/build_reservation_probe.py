"""Private observer overlay over the historical structured-writer executable."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path
BASE='4073cae36981ce2bed73a3319376323657c99a167b9fc81198d8a3cfe1cbff25'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if hashlib.sha256(a.base.read_bytes()).hexdigest()!=BASE:raise ValueError('Exact historical executable required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    a.output.parent.mkdir(parents=True,exist_ok=True);root=Path(__file__).resolve().parent
    exports=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED']
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        d=Path(td);sources=[root/'ReservationProbe.java',root/'ReservationProbeInstrumenter.java']
        subprocess.run(['java',*exports,'-m','jdk.compiler/com.sun.tools.javac.Main',*exports,'-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True)
        entry='forge/ai/ComputerUtilMana.class'
        with zipfile.ZipFile(a.base) as z:(d/'original.class').write_bytes(z.read(entry))
        subprocess.run(['java',*exports,'-cp',td+':'+str(a.base.resolve()),'ReservationProbeInstrumenter',str(d/'original.class'),str(d/'patched.class')],check=True)
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x') as new:
            for info in old.infolist():new.writestr(info,(d/'patched.class').read_bytes() if info.filename==entry else old.read(info.filename))
            new.writestr('ReservationProbe.class',(d/'ReservationProbe.class').read_bytes())
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output) as new:
            assert new.testzip() is None and all(old.read(n)==new.read(n) for n in old.namelist() if n!=entry)
        report=dict(base_sha256=BASE,sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),changed_entries=[entry],added_entries=['ReservationProbe.class'],other_entries_byte_identical=True,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
