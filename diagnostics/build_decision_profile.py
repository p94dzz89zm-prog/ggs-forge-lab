"""Build an isolated diagnostic overlay; never edit production sources."""
from pathlib import Path
import re, subprocess, sys

def end_brace(text,start):
    depth=0; state='code'; i=start
    while i<len(text):
        c=text[i]; pair=text[i:i+2]
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

def instrument(text,method,label,arity=None):
    found=0
    matches=list(re.finditer(r'^    (?:public|private|protected)[^\n]*\b'+method+r'\s*\(',text,re.M))
    for m in reversed(matches):
        opening=text.index('{',m.start()); end=end_brace(text,opening)
        params=text[text.index('(',m.start())+1:text.index(')',m.start())]
        # Count commas outside generic type arguments.
        plain=re.sub(r'<[^<>]*>','',params)
        if arity is not None and (plain.count(',')+1 if plain.strip() else 0)!=arity:continue
        text=text[:end]+'\n        }\n    '+text[end:]
        argument='"'+label+'"'
        if label=='static-rebuild':argument='preList.isEmpty() ? "static-rebuild-live" : "static-rebuild-hypothetical"'
        text=text[:opening+1]+'\n        try(var dmTiming=forge.diagnostics.DecisionProfiler.enter('+argument+')) {'+text[opening+1:]
        found+=1
    assert found,(method,arity)
    return text

if __name__=='__main__':
    src,jar,out=map(Path,sys.argv[1:4]); out.mkdir(parents=True,exist_ok=True)
    files={
      'forge-ai/src/main/java/forge/ai/AiController.java':[
        ('chooseSpellAbilityToPlay','choose-action',0),('doTrigger','choose-trigger',2),
        ('declareAttackers','choose-attack',2),('declareBlockersFor','choose-block',2),
        ('canPlayAndPayFor','candidate-pay',None),('canPlaySa','candidate-play',None)],
      'forge-ai/src/main/java/forge/ai/AiAttackController.java':[('declareAttackers','attack-search',None)],
      'forge-ai/src/main/java/forge/ai/AiBlockController.java':[('assignBlockersForCombat','block-search',2)],
      'forge-ai/src/main/java/forge/ai/ComputerUtil.java':[
        ('predictNextCombatsRemainingLife','forecast-combat',6),('evaluateBoardPositionChanged','forecast-board',2)],
      'forge-ai/src/main/java/forge/ai/ComputerUtilAbility.java':[('getSpellAbilities','discover-abilities',2)],
      'forge-game/src/main/java/forge/game/card/Card.java':[('getAllPossibleAbilities','card-abilities',3)],
      'forge-game/src/main/java/forge/game/GameActionUtil.java':[('getAlternativeCosts','alternative-costs',3)],
      'forge-game/src/main/java/forge/game/GameAction.java':[('checkStaticAbilities','static-rebuild',3)],
      'forge-game/src/main/java/forge/game/ability/AbilityUtils.java':[('resolve','resolve-action',1)],
    }
    if '--blocking' in sys.argv[4:]:
        files['forge-game/src/main/java/forge/game/combat/CombatUtil.java']=[
            ('canBlock','block-legality',None),('getBlockCost','block-cost',3),
            ('mustBlockAnAttacker','block-requirements',3),('canBeBlocked','attacker-blockability',None)]
    if '--block-internals' in sys.argv[4:]:
        files['forge-ai/src/main/java/forge/ai/AiBlockController.java'] += [
            (name, 'block-'+name, None) for name in (
                'assignBlockers','getPossibleBlockers','getSafeBlockers','getKillingBlockers',
                'sortPotentialAttackers','makeGoodBlocks','makeGangBlocks','makeGangNonLethalBlocks',
                'makeTradeBlocks','makeChumpBlocks','makeMultiChumpBlocks',
                'reinforceBlockersAgainstTrample','reinforceBlockersToKill',
                'makeChumpBlocksToSavePW','makeRequiredBlocks','removeUnpayableBlocks')]
        files['forge-ai/src/main/java/forge/ai/ComputerUtilCombat.java'] = [
            ('canDestroyAttacker','destroy-attacker',6),('canDestroyBlocker','destroy-blocker',6),
            ('predictDamageTo','predict-damage',5),('lifeInDanger','life-danger',3)]
        files['forge-ai/src/main/java/forge/ai/ComputerUtilCard.java'] = [
            ('evaluateCreature','evaluate-creature',1)]
    sources=[]
    for path,methods in files.items():
        text=(src/path).read_text()
        for method,label,arity in methods:text=instrument(text,method,label,arity)
        if Path(path).name=='AiController.java':
            original='return future.get(game.getAITimeout(), TimeUnit.SECONDS);'
            assert text.count(original)==1
            text=text.replace(original,'try(var dmWait=forge.diagnostics.DecisionProfiler.enter("candidate-wait")) { '+original+' }')
        if Path(path).name=='GameActionUtil.java':
            statements={
              'game.getAction().checkStaticAbilities(false, Sets.newHashSet(source), preList);':'alternate-face-rebuild',
              'game.getAction().checkStaticAbilities(false, Sets.newHashSet(stackCopy), preList);':'stack-keyword-rebuild',
              'game.getAction().checkStaticAbilities(false);':'restore-live-state',
            }
            for original,label in statements.items():
                assert text.count(original)>=1,(label,text.count(original))
                text=text.replace(original,'try(var dmRebuild=forge.diagnostics.DecisionProfiler.enter("'+label+'")) { '+original+' }')
        dest=out/Path(path).name;dest.write_text(text);sources.append(dest)
    sources.append(Path(__file__).with_name('DecisionProfiler.java'))
    classes=out/'classes';classes.mkdir(exist_ok=True)
    subprocess.run(['java','com.sun.tools.javac.Main','-cp',str(jar.resolve()),'-d',str(classes),*map(str,sources)],check=True)
    print('Diagnostic overlay:',classes.resolve())
