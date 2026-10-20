"""Default-off causal allocation diagnostic overlay; preserves exact base engine."""
import argparse,hashlib,json,subprocess,tempfile,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EXPORTS=['--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED','--add-exports=java.base/jdk.internal.org.objectweb.asm.commons=ALL-UNNAMED']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if sha(a.base)!=a.sha256:raise ValueError('Exact base hash required')
    if a.output.exists() or Path('/workspace') in a.output.resolve().parents:raise ValueError('Fresh isolated output required')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=a.output.parent) as temp:
        t=Path(temp);classes=t/'classes';classes.mkdir();subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main',*EXPORTS,'-cp',str(a.base),'-d',str(classes),str(ROOT/'CardAllocationTraceInstrumenter.java'),str(ROOT/'pilot-src/forge/ai/bridge/CardAllocationTrace.java')],check=True)
        with zipfile.ZipFile(a.base) as z:(t/'Game.class').write_bytes(z.read('forge/game/Game.class'))
        subprocess.run(['java',*EXPORTS,'-cp',str(classes)+':'+str(a.base),'CardAllocationTraceInstrumenter',str(t/'Game.class'),str(t/'Game.traced.class')],check=True)
        with zipfile.ZipFile(a.base) as old,zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():new.writestr(entry,(t/'Game.traced.class').read_bytes() if entry.filename=='forge/game/Game.class' else old.read(entry.filename))
            new.writestr('forge/ai/bridge/CardAllocationTrace.class',(classes/'forge/ai/bridge/CardAllocationTrace.class').read_bytes())
    report=dict(base_sha256=a.sha256,sha256=sha(a.output),default_enabled=False,property='forge.evidence.traceCardAllocation',scope='Allocation/counter trace only; no identity correction or game approval',source_sha256={str(s.relative_to(ROOT)):sha(s) for s in [ROOT/'CardAllocationTraceInstrumenter.java',ROOT/'pilot-src/forge/ai/bridge/CardAllocationTrace.java',Path(__file__)]})
    a.output.with_suffix('.build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
