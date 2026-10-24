import forge.ai.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Available-card post-wipe constructed comparison, not a deck win-rate test. */
public class WhipRecoveryDecisionRegression extends PackageRecoveryRegression {
 void recover(boolean fourBlack,boolean floatGeneric){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(2);for(Player p:g.getPlayers())fillLibrary(p,30);ai.setLife(7,null);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  for(String n:fourBlack?List.of("Swamp","Swamp","Swamp","Swamp","Island","Island","Island","Mountain"):List.of("Swamp","Swamp","Swamp","Swamp","Swamp","Swamp","Island","Mountain"))addCard(n,ai);
  Card breath=addCardToZone("Breath of Fury",ai,ZoneType.Hand),whip=addCardToZone("Whip of Erebos",ai,ZoneType.Hand),grave=addCardToZone("Baleful Strix",ai,ZoneType.Graveyard);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  SpellAbility aura=breath.getFirstSpellAbility();aura.setActivatingPlayer(ai);Assert.assertTrue(g.getCardsIn(ZoneType.Battlefield).stream().noneMatch(aura::canTarget),"empty creature board gives Breath no legal target");
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();System.out.println("WHIP_DECISION initial="+(choices==null?"none":choices));
  // Record the real controller choice, then test the available legal recovery
  // independently; neither an unavailable-card game nor a chosen-card reward.
  boolean choseWhip=choices!=null&&choices.size()==1&&choices.get(0).getHostCard()==whip;
  if(floatGeneric){int count=0;for(Card land:ai.getLandsInPlay())if(land.getName().equals("Island")&&count++<2){SpellAbility mana=land.getManaAbilities().get(0);mana.setActivatingPlayer(ai);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,mana,null));drain(g);Assert.assertTrue(land.isTapped());}}
  Card resolved=cast(ai,whip);System.out.println("WHIP_DECISION afterCast="+((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay());SpellAbility rise=resolved.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElseThrow();rise.setActivatingPlayer(ai);Assert.assertTrue(rise.canTarget(grave));rise.getTargets().add(grave);
  if(fourBlack&&!floatGeneric){Assert.assertFalse(ComputerUtilCost.canPayCost(rise,ai,false),"greedy cast consumed black mana needed for activation");groups++;System.out.println("WHIP_PAYMENT fourBlack=true floatedGeneric=false activationPayable=false preservedFailure=true");return;}
  play(ai,rise);
  Card strix=permanent(ai,"Baleful Strix");Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),8L);Assert.assertTrue(CombatUtil.canAttack(strix,opp));Assert.assertTrue(strix.hasKeyword(forge.game.keyword.Keyword.LIFELINK));
  Combat combat=new Combat(ai);combat.addAttacker(strix,opp);combat.setBlocked(strix,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));combat.assignCombatDamage(false);combat.dealAssignedDamage();drain(g);Assert.assertEquals(ai.getLife(),8);Assert.assertEquals(opp.getLife(),19);Assert.assertTrue(ai.getCardsIn(ZoneType.Hand).size()>=2,"Strix ETB drew a card with Breath retained");
  groups++;System.out.println("WHIP_RECOVERY actualInitialChoiceWhip="+choseWhip+" paid8 gained1 bodyReturned1 commanderAbsent=true fourBlack="+fourBlack+" floatedGeneric="+floatGeneric);
 }
 public static void main(String[]args){var t=new WhipRecoveryDecisionRegression();t.initializeModel();t.recover(false,false);t.recover(true,false);t.recover(true,true);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
