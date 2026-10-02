"""Build an isolated diagnostic overlay; no production files are modified."""
from pathlib import Path
import subprocess, sys
def end_brace(text,start):
    depth=0;state='code';i=start
    while i<len(text):
        c=text[i];pair=text[i:i+2]
        if state=='line':
            if c=='\n':state='code'
        elif state=='block':
            if pair=='*/':state='code';i+=1
        elif state in ('"',"'"):
            if c=='\\':i+=1
            elif c==state:state='code'
        elif pair=='//':state='line';i+=1
        elif pair=='/*':state='block';i+=1
        elif c in ('"',"'"):state=c
        elif c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return i
        i+=1
    raise ValueError('Unbalanced body')
src, jar, out = map(Path, sys.argv[1:4])
out.mkdir(parents=True, exist_ok=True)
def wrap(text, marker, prefix, suffix=''):
    start = text.index('{', text.index(marker)); end = end_brace(text, start)
    return text[:start+1] + '\n' + prefix + text[start+1:end] + '\n' + suffix + '\n}' + text[end+1:]
path = 'forge-game/src/main/java/forge/game/GameActionUtil.java'
text = (src/path).read_text()
marker = 'if (game.getAction().hasStaticAbilityAffectingZone(ZoneType.Stack, StaticAbilityLayer.ABILITIES)'
text = wrap(text, marker, 'try(var dmRebuild=forge.diagnostics.StackEligibilityProfiler.query(source,activator)) {\nint dmBefore=alternatives.size();', 'dmRebuild.completed(alternatives.size()-dmBefore);\n}')
dest = out/'GameActionUtil.java'; dest.write_text(text)
path = 'forge-ai/src/main/java/forge/ai/ComputerUtilAbility.java'
text = (src/path).read_text()
for method in ['getSpellAbilities(', 'getOriginalAndAltCostAbilities(']:
    text = wrap(text, 'public static List<SpellAbility> '+method, 'try(var dmDiagnosticDiscovery=forge.diagnostics.StackEligibilityProfiler.search()) {', '}')
other = out/'ComputerUtilAbility.java'; other.write_text(text)
classes = out/'classes'; classes.mkdir(exist_ok=True)
subprocess.run(['java','com.sun.tools.javac.Main','-cp',str(jar.resolve()),'-d',str(classes),str(dest),str(other),str(Path(__file__).with_name('StackEligibilityProfiler.java'))],check=True)
print('Diagnostic overlay:',classes.resolve())
