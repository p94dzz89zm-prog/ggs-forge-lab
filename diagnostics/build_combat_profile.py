from pathlib import Path
import re, subprocess, sys

src,jar,out=map(Path,sys.argv[1:4]);out.mkdir(parents=True,exist_ok=True)
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
def edits(text,name,scope=None,enter=None,deep=False):
    starts=list(re.finditer(r'^    (?:public|private|protected)[^\n]*\b'+name+r'\s*\(',text,re.M))
    assert starts,name
    for m in reversed(starts):
        opening=text.index('{',m.start());end=end_brace(text,opening)
        params=text[text.index('(',m.start())+1:text.index(')',m.start())]
        if deep and params.count(',')!=5:continue
        if scope:
            text=text[:end]+'\n        }\n    '+text[end:]
            text=text[:opening+1]+'\n        try(var dmProfile='+scope+') {'+text[opening+1:]
        else:text=text[:opening+1]+'\n        '+enter+text[opening+1:]
    return text
files={
 'forge-ai/src/main/java/forge/ai/AiController.java':['canPlayAndPayFor','canPlaySa'],
 'forge-ai/src/main/java/forge/ai/AiBlockController.java':['assignBlockersForCombat'],
 'forge-ai/src/main/java/forge/ai/AiAttackController.java':['declareAttackers'],
 'forge-ai/src/main/java/forge/ai/ComputerUtil.java':['predictNextCombatsRemainingLife'],
}
sources=[]
for path,methods in files.items():
    text=(src/path).read_text()
    for name in methods:text=edits(text,name,scope='forge.diagnostics.CombatWorkProfiler.search()')
    dest=out/Path(path).name;dest.write_text(text);sources.append(dest)
path='forge-ai/src/main/java/forge/ai/ComputerUtilCombat.java';text=(src/path).read_text()
for name in ['canDestroyAttacker','canDestroyBlocker']:
    text=edits(text,name,deep=True,scope='forge.diagnostics.CombatWorkProfiler.pair("'+name+'",ai,attacker,blocker,combat,withoutAbilities,withoutAttackerStaticAbilities)')
dest=out/'ComputerUtilCombat.java';dest.write_text(text);sources.append(dest)
path='forge-game/src/main/java/forge/game/replacement/ReplacementHandler.java';text=edits((src/path).read_text(),'invalidateReadOnlyManaInspection',enter='forge.diagnostics.CombatWorkProfiler.invalidate();')
dest=out/'ReplacementHandler.java';dest.write_text(text);sources.append(dest)
path='forge-game/src/main/java/forge/game/combat/Combat.java';text=(src/path).read_text()
for name in ['endCombat','clearAttackers','addAttacker','setBlocked','addBlocker','removeBlockAssignment','undoBlockingAssignment','orderBlockersForDamageAssignment','addBlockerToDamageAssignmentOrder','orderAttackersForDamageAssignment','unregisterAttacker','unregisterDefender','removeFromCombat','removeAbsentCombatants','assignCombatDamage','dealAssignedDamage']:
    text=edits(text,name,enter='forge.diagnostics.CombatWorkProfiler.combatChanged(this);')
dest=out/'Combat.java';dest.write_text(text);sources.append(dest)
sources.append(Path(__file__).with_name('CombatWorkProfiler.java'))
classes=out/'classes';classes.mkdir(exist_ok=True)
subprocess.run(['java','com.sun.tools.javac.Main','-cp',str(jar.resolve()),'-d',str(classes),*map(str,sources)],check=True)
print('Diagnostic overlay:',classes.resolve())
