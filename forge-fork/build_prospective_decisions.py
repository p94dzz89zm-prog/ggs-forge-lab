"""Add offline decision offers and first-priority capture to exact Stage58 runtime."""
import argparse,hashlib,json,os,subprocess,tempfile,zipfile
from pathlib import Path
BASE='e6d110c313cb85de00d7d6637d35ff2446347fbd6dddc95ab9457b0bc3eb6311'
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
    if sha(a.base)!=BASE or a.output.exists():raise ValueError('Exact capture base and fresh output required')
    root=Path(__file__).resolve().parent;sources=[root/'ProspectiveDecisionInstrumenter.java',root/'pilot-src/forge/ai/bridge/ProspectiveDecisionEvidence.java',root/'pilot-src/forge/ai/bridge/ProspectiveOpeningEvidence.java'];exports=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED','--add-exports=java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED'];a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as td:
        work=Path(td);subprocess.run(['java',*exports,'-m','jdk.compiler/com.sun.tools.javac.Main',*exports,'-cp',str(a.base.resolve()),'-d',td,*map(str,sources)],check=True);changes={x.relative_to(work).as_posix():x.read_bytes()for x in(work/'forge').rglob('*.class')}
        for cls in ['forge/game/Game','forge/ai/PlayerControllerAi','forge/ai/validation/RulesValidationController']:
            name=cls+'.class';before=work/'before.class';after=work/'after.class'
            with zipfile.ZipFile(a.base)as old:before.write_bytes(old.read(name))
            subprocess.run(['java',*exports,'-cp',td+os.pathsep+str(a.base.resolve()),'ProspectiveDecisionInstrumenter',str(before),str(after)],check=True);changes[name]=after.read_bytes();after.unlink()
        with zipfile.ZipFile(a.base)as old,zipfile.ZipFile(a.output,'x')as new:
            for info in old.infolist():new.writestr(info,changes.get(info.filename,old.read(info)))
            for name in sorted(set(changes)-set(old.namelist())):
                info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;new.writestr(info,changes[name])
        with zipfile.ZipFile(a.base)as old,zipfile.ZipFile(a.output)as new:assert new.testzip()is None and all(old.read(n)==new.read(n)for n in old.namelist()if n not in changes)
        report=dict(base_sha256=BASE,output_sha256=sha(a.output),changed_classes={n:hashlib.sha256(b).hexdigest()for n,b in changes.items()},source_sha256={str(s.relative_to(root)):sha(s)for s in sources},other_entries_byte_identical=True,full_game_rules_approved=False)
        a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
