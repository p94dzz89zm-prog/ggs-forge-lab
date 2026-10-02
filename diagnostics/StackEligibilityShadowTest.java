package forge.ai;

import forge.diagnostics.StackEligibilityProfiler;
import forge.game.card.Card;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Regression cases for the shadow classifier, not a universal rules proof. */
public class StackEligibilityShadowTest extends AITest {
    private Card hand(String name,forge.game.player.Player player){return addCardToZone(name,player,ZoneType.Hand);}
    @Test public void nonAssassinIsExcludedAndRealAssassinKept(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);
        addCard("Ezio Auditore da Firenze",p);
        Assert.assertTrue(StackEligibilityProfiler.predict(hand("Grizzly Bears",p),p).skip());
        Assert.assertFalse(StackEligibilityProfiler.predict(hand("Basim Ibn Ishaq",p),p).skip());
    }
    @Test public void otherControllerAssassinExcludedButBorrowedSpellFallsBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);var other=game.getPlayers().get(1);
        addCard("Ezio Auditore da Firenze",p);Card candidate=hand("Basim Ibn Ishaq",other);
        Assert.assertTrue(StackEligibilityProfiler.predict(candidate,other).skip());
        Assert.assertEquals(StackEligibilityProfiler.predict(candidate,p).reason(),"borrowed-candidate");
    }
    @Test public void lkiAndChangelingCandidatesFallBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card candidate=hand("Grizzly Bears",p);
        Assert.assertEquals(StackEligibilityProfiler.predict(forge.game.card.CardCopyService.getLKICopy(candidate),p).reason(),"lki-candidate");
        Assert.assertFalse(StackEligibilityProfiler.predict(hand("Changeling Outcast",p),p).skip());
    }
    @Test public void activeTypeChangerInLibraryBlocksPrediction(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCardToZone("Grizzly Bears",p,ZoneType.Library);
        host.addStaticAbility("Mode$ Continuous | Affected$ Card.YouCtrl | AffectedZone$ Hand | EffectZone$ Library | AddType$ Assassin");
        Assert.assertEquals(StackEligibilityProfiler.predict(hand("Grizzly Bears",p),p).reason(),"type-layer");
    }
    @Test public void controlAndTextChangesBlockPrediction(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);Card host=addCard("Grizzly Bears",p);addCard("Ezio Auditore da Firenze",p);
        Card candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | GainControl$ True");
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | ChangeColorWordsTo$ Blue");
        String reason=StackEligibilityProfiler.predict(candidate,p).reason();
        Assert.assertTrue(reason.contains("control-layer"));Assert.assertTrue(reason.contains("text-layer"));
    }
    @Test public void unknownStackAndDefinedGrantsFallBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p);Card candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | AffectedDefined$ Remembered | AddKeyword$ Freerunning:B B");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void descriptorMutationIsSeenWithinScope(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);Card ezio=addCard("Ezio Auditore da Firenze",p);Card candidate=hand("Grizzly Bears",p);
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            var grant=ezio.getStaticAbilities().stream().filter(s->s.hasParam("AffectedZone")).findFirst().orElseThrow();
            grant.putParam("Affected","Card.YouCtrl+wasCast");
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void controllerMutationIsSeenWithinScope(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);var other=game.getPlayers().get(1);
        Card ezio=addCard("Ezio Auditore da Firenze",p),candidate=hand("Basim Ibn Ishaq",other);
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,other).skip());
            ezio.setController(other,game.getNextTimestamp());
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,other).skip());
        }
    }
    @Test public void generatedStaticSVarMutationIsSeenWithinScope(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.setSVar("Generated","Mode$ Continuous | Affected$ Creature.YouCtrl | AddPower$ 1");
        host.addStaticAbility("Mode$ Continuous | Affected$ Creature.YouCtrl | AddStaticAbility$ Generated");
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            host.setSVar("Generated","Mode$ Continuous | Affected$ Card | AffectedZone$ Stack | AddKeyword$ Freerunning:B B");
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void addedHiddenSourceIsSeenWithinScope(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);Card candidate=hand("Grizzly Bears",p);
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            Card hidden=addCardToZone("Grizzly Bears",p,ZoneType.Library);
            hidden.addStaticAbility("Mode$ Continuous | EffectZone$ Library | Affected$ Card | AffectedZone$ Stack | AddKeyword$ Freerunning:B B");
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void unknownGeneratedTraitsAndVariablesFallBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.setSVar("Variable","SVar:Foo:Count$Valid Card");
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | AddSVar$ Variable");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void abilityRemovalFallsBackEvenOffBoard(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCardToZone("Grizzly Bears",p,ZoneType.Hand),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Creature | EffectZone$ Hand | RemoveAllAbilities$ True");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void unrecognizedKeywordGeneratorFallsBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Creature | AddKeyword$ Changeling");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void alwaysTriggerSVarMutationFallsBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.setSVar("Generated","Mode$ DamageDone | ValidSource$ Card.Self | Execute$ None");
        host.addStaticAbility("Mode$ Continuous | Affected$ Creature | AddTrigger$ Generated");
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            host.setSVar("Generated","Mode$ Always | Execute$ None");
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void fixedInactiveSourceIsExcludedButCandidateStackActivationFallsBack(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card hidden=addCardToZone("Grizzly Bears",p,ZoneType.Library),candidate=hand("Grizzly Bears",p);
        hidden.addStaticAbility("Mode$ Continuous | Affected$ Card | AffectedZone$ Hand | AddType$ Assassin");
        Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
        candidate.addStaticAbility("Mode$ Continuous | EffectZone$ Stack | Affected$ Card.Self | AffectedZone$ Stack | AddType$ Assassin");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void inactiveUnknownStackSourceBecomesRelevantOnZoneChange(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCardToZone("Grizzly Bears",p,ZoneType.Library),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | AffectedZone$ Stack | AddKeyword$ Freerunning:B B");
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            p.getZone(ZoneType.Library).remove(host);p.getZone(ZoneType.Battlefield).add(host);host.setZone(p.getZone(ZoneType.Battlefield));
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void compoundCharacteristicEffectCannotHideGeneratedGrant(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.setSVar("Generated","Mode$ Continuous | Affected$ Card | AffectedZone$ Stack | AddKeyword$ Freerunning:B B");
        host.addStaticAbility("Mode$ Continuous | CharacteristicDefining$ True | AddType$ Assassin | AddStaticAbility$ Generated");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void unrelatedEquipmentIsExcludedAndAttachmentMutationIsSeen(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card equipment=addCard("Lightning Greaves",p),bear=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        equipment.setEntityAttachedTo(bear);
        try(var scope=StackEligibilityProfiler.search()){
            Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
            equipment.setEntityAttachedTo(candidate);
            Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
        }
    }
    @Test public void unrelatedSelfTypeEffectIsExcludedButCandidateTargetIsNot(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | AffectedDefined$ Self | AddType$ Assassin");
        Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
        candidate.addStaticAbility("Mode$ Continuous | EffectZone$ Hand | AffectedDefined$ Self | AddType$ Assassin");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void definedSelectorDoesNotHideAbilityRewrite(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | AffectedDefined$ Self | RemoveAllAbilities$ True");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void removedSourceTraitsCannotDisappearFromDependencyAudit(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.addStaticAbility("Mode$ Continuous | Affected$ Card | AffectedZone$ Stack | AddType$ Assassin");
        host.addChangedCardTraits(null,null,null,null,trait->true,game.getNextTimestamp(),99L);
        Assert.assertTrue(host.getStaticAbilities().isEmpty());
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void removedSourceKeywordsCannotDisappearFromDependencyAudit(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        Card host=addCard("Grizzly Bears",p),candidate=hand("Grizzly Bears",p);
        host.addChangedCardKeywords(java.util.List.of(),java.util.List.of("Flying"),false,game.getNextTimestamp(),null);
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    @Test public void shadowQueryDoesNotChangeAlternativeCostResults(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);addCard("Ezio Auditore da Firenze",p);
        for(String name:new String[]{"Grizzly Bears","Basim Ibn Ishaq"}){
            Card candidate=hand(name,p);var sa=candidate.getFirstSpellAbility();sa.setActivatingPlayer(p);
            var first=forge.game.GameActionUtil.getAlternativeCosts(sa,p,false);
            var second=forge.game.GameActionUtil.getAlternativeCosts(sa,p,false);
            Assert.assertEquals(signature(first),signature(second));
        }
    }
    @Test public void borrowedNonAssassinCanBeExcludedWithoutAssumingCastController(){
        var game=initAndCreateGame();var p=game.getPlayers().get(0);var other=game.getPlayers().get(1);
        addCard("Ezio Auditore da Firenze",p);
        Card candidate=hand("Grizzly Bears",other);
        Assert.assertTrue(StackEligibilityProfiler.predict(candidate,p).skip());
        candidate.addStaticAbility("Mode$ Continuous | EffectZone$ Stack | AffectedDefined$ Self | AddType$ Assassin");
        Assert.assertFalse(StackEligibilityProfiler.predict(candidate,p).skip());
    }
    private java.util.List<String> signature(java.util.List<forge.game.spellability.SpellAbility> values){return values.stream().map(sa->sa.getAlternativeCost()+":"+sa.getPayCosts()+":"+sa.getRestrictions().getZone()).toList();}
}
