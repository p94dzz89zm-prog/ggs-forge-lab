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
        plain=params
        while re.search(r'<[^<>]*>',plain):
            plain=re.sub(r'<[^<>]*>','',plain)
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
    static_internals = any(flag in sys.argv[4:] for flag in ('--static-internals', '--affected-internals', '--validity-internals'))
    if static_internals:
        files['forge-game/src/main/java/forge/game/GameAction.java'] += [
            ('findStaticAbilityToApply','static-dependencies',5)]
        files['forge-game/src/main/java/forge/game/StaticEffects.java'] = [
            ('clearStaticEffects','static-clear',2),('removeStaticEffect','static-undo',3)]
        files['forge-game/src/main/java/forge/game/staticability/StaticAbility.java'] = [
            ('applyContinuousAbilityBefore','static-apply-before',2),('applyContinuousAbility','static-apply',2)]
        files['forge-game/src/main/java/forge/game/staticability/StaticAbilityContinuous.java'] = [
            ('getAffectedCards','static-affected-cards',2),('getAffectedPlayers','static-affected-players',1),
            ('applyContinuousAbility','static-effect-body',3)]
    if '--validity-internals' in sys.argv[4:]:
        files['forge-game/src/main/java/forge/game/card/CardLists.java'] = []
    sources=[]
    for path,methods in files.items():
        text=(src/path).read_text()
        for method,label,arity in methods:text=instrument(text,method,label,arity)
        if Path(path).name=='AiController.java':
            original='return future.get(game.getAITimeout(), TimeUnit.SECONDS);'
            assert text.count(original)==1
            text=text.replace(original,'try(var dmWait=forge.diagnostics.DecisionProfiler.enter("candidate-wait")) { '+original+' }')
        if static_internals and Path(path).name=='GameAction.java':
            begin='        game.forEachCardInGame(c -> {'
            assert text.count(begin)==1
            start=text.index(begin);end=text.index('        }, true);',start)+len('        }, true);')
            text=text[:start]+'        try(var dmCollect=forge.diagnostics.DecisionProfiler.enter("static-collect")) {\n'+text[start:end]+'\n        }'+text[end:]
        if any(flag in sys.argv[4:] for flag in ('--affected-internals', '--validity-internals')) and Path(path).name=='StaticAbilityContinuous.java':
            start=text.index('    public static CardCollectionView getAffectedCards(')
            opening=text.index('{',start);end=end_brace(text,opening)
            body=text[opening+1:end]
            ranges=[
                ('        if (stAb.isCharacteristicDefining()) {','        // non - CharacteristicDefining','affected-cda'),
                ('        if (stAb.hasParam("AffectedDefined")) {','        // add preList','affected-defined'),
                ('        if (!preList.isEmpty()) {','        final CardCollectionView zoneCards;','affected-hypothetical'),
                ('        if (stAb.hasParam("AffectedDefined")) {\n            zoneCards','        // With no selected','affected-zones'),
                ('        if (affectedCards.isEmpty()) {','        if (stAb.hasParam("Affected")) {','affected-union'),
                ('            if (controller.hasKeyword("Shaman\'s Trance")','            affectedCards = CardLists.getValidCards','affected-trance-guard'),
                ('            if (affectedCardsOriginal != null) {','        } else if (candidates != affectedCards) {','affected-trance-addback'),
            ]
            for begin,finish,label in ranges:
                a=body.index(begin);b=body.index(finish,a)
                body=body[:a]+'        try(var dmPart=forge.diagnostics.DecisionProfiler.enter("'+label+'")) {\n'+body[a:b]+'        }\n'+body[b:]
            for original,label in [
                ('            affectedCards = CardLists.getValidCards(candidates, stAb.getParam("Affected"), controller, hostCard, stAb);','affected-validity'),
                ('        affectedCards.removeAll(stAb.getIgnoreEffectCards());','affected-ignore')]:
                assert body.count(original)==1
                body=body.replace(original,'        try(var dmPart=forge.diagnostics.DecisionProfiler.enter("'+label+'")) {\n'+original+'\n        }')
            text=text[:opening+1]+body+text[end:]
        if '--validity-internals' in sys.argv[4:] and Path(path).name=='CardLists.java':
            original='        return CardLists.filter(cardList, Card.validityPredicate(restriction, sourceController, source, sa));'
            prepare='Card.validityPredicate(restriction, sourceController, source, sa)'
            if text.count(original)==0:
                prepare='CardPredicates.restriction(restriction.split(","), sourceController, source, sa)'
                original='        return CardLists.filter(cardList, '+prepare+');'
            assert text.count(original)==1
            text=text.replace(original, '\n'.join([
                '        try(var dmSample=forge.diagnostics.DecisionProfiler.beginValiditySample()) {',
                '            final java.util.function.Predicate<Card> predicate;',
                '            try(var dmPrepare=forge.diagnostics.DecisionProfiler.enter("validity-query-preparation")) {',
                '                predicate='+prepare+';',
                '            }',
                '            try(var dmFilter=forge.diagnostics.DecisionProfiler.enter("validity-query-filter")) {',
                '                return CardLists.filter(cardList, predicate);',
                '            }',
                '        }']))
        if '--validity-internals' in sys.argv[4:] and Path(path).name=='Card.java':
            lookup='        ParsedValidity parsed = VALIDITY_SYNTAX.getUnchecked(restriction);'
            if lookup in text:
                text=text.replace(lookup, '        final ParsedValidity parsed;\n        try(var dmSyntax=forge.diagnostics.DecisionProfiler.inValiditySample() ? forge.diagnostics.DecisionProfiler.enter("validity-syntax-lookup") : null) {\n            parsed = VALIDITY_SYNTAX.getUnchecked(restriction);\n        }')
            begin='        // need to filter out prepared spells for other cards'
            finish='        if (parsed.properties() != null) {'
            a=text.index(begin);b=text.index(finish,a)
            text=text[:a]+'        try(var dmType=forge.diagnostics.DecisionProfiler.inValiditySample() ? forge.diagnostics.DecisionProfiler.enter("validity-type") : null) {\n'+text[a:b]+'        }\n'+text[b:]
            start=text.index('    public boolean hasProperty(final String property,')
            opening=text.index('{',start);end=end_brace(text,opening)
            text=text[:end]+'\n        }\n    '+text[end:]
            text=text[:opening+1]+'\n        try(var dmProperty=forge.diagnostics.DecisionProfiler.inValiditySample() ? forge.diagnostics.DecisionProfiler.enter("validity-property-"+property.replace(",", ";")) : null) {'+text[opening+1:]
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
