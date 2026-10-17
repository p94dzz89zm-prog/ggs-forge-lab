import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.Keyword;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Diagnostic constructed boundary; not a heldout strength evaluation. */
public class ExileCounterRescueRegression extends CounterRescuePaymentRegression {
 boolean baseline;
 int groups;
 void scenario(String counterName,int removerLife) {
  int mode=0;boolean manualPass=false;
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");
  for(Player p:g.getPlayers())fillLibrary(p,20);int life=mode==1?7:5;ai.setLife(life,null);remover.setLife(removerLife,null);
  Card target=addCard("Colossal Dreadmaw",enemy),other=addCard("Grizzly Bears",enemy),shield=addCard(mode==2?"White Knight":"Memnite",ai);
  for(Card body:List.of(target,other,shield)){body.setSickness(false);body.setTurnInZone(-1);}
  g.getAction().checkStateEffects(true);

  Card counter=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);combat.addAttacker(target,ai);combat.addAttacker(other,ai);combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  var removal=addCardToZone("Anguished Unmaking",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canPlay());Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();boolean countered=!manualPass&&choice!=null;
  Assert.assertEquals(choice!=null,baseline,"actual automatic exile rescue choice");
  if(countered){var cast=choice.get(0);Assert.assertEquals(cast.getHostCard(),counter);Assert.assertTrue(cast.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(cast,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),countered);
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),countered?(counterName.equals("Counterspell")?2L:1L):0L);
  Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(b->b.isToken()&&b.getName().contains("Treasure")).count(),countered&&counterName.equals("An Offer You Can't Refuse")?2L:0L);
  combat.assignCombatDamage(true);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);drain(g);
  if(ai.getLife()>0){combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);}
  Assert.assertEquals(ai.getLife(),countered?-2:3);Assert.assertEquals(remover.getLife(),countered?removerLife:removerLife-3);Assert.assertEquals(target.isInZone(ZoneType.Exile),!countered);Assert.assertEquals(counter.isInZone(ZoneType.Hand),!countered);groups++;
  System.out.println("EXILE_COUNTER mode="+mode+" card="+counterName+" manualPass="+manualPass+" automaticChoice="+(choice!=null)+" countered="+countered+" finalLife="+ai.getLife());
 }
 void protection(String counterName,boolean ownTarget) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(ownTarget?5:20,null);remover.setLife(40,null);
  Card attacker=addCard("Colossal Dreadmaw",enemy),blocker=addCard("Goro-Goro and Satoru",ai);attacker.setSickness(false);blocker.setSickness(false);Combat combat=new Combat(enemy);combat.addAttacker(attacker,ai);if(ownTarget){combat.addBlocker(attacker,blocker);combat.setBlocked(attacker,true);}else combat.setBlocked(attacker,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  Card counterCard=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);var removal=addCardToZone("Anguished Unmaking",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(ownTarget?blocker:attacker);Assert.assertTrue(removal.canTarget(ownTarget?blocker:attacker));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));var counter=counterCard.getFirstSpellAbility();counter.setActivatingPlayer(ai);Assert.assertFalse(forge.ai.ggs.GgsCounterRescuePolicy.rejectLethalRescueCounter(ai,counter));var pilot=((PlayerControllerAi)ai.getController()).getAi();
  if(ownTarget){var choice=pilot.chooseSpellAbilityToPlay();Assert.assertNotNull(choice,"protect own indispensable blocker");Assert.assertEquals(choice.get(0).getHostCard(),counterCard);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,choice.get(0),null));drain(g);Assert.assertTrue(blocker.isInZone(ZoneType.Battlefield));Assert.assertEquals(remover.getLife(),40);combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);Assert.assertEquals(ai.getLife(),3);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),counterName.equals("Counterspell")?2L:1L);}
  else{var decision=pilot.canPlaySa(counter);System.setProperty("dragonmind.disableCounterRescuePolicy","true");Assert.assertEquals(pilot.canPlaySa(counter),decision);System.clearProperty("dragonmind.disableCounterRescuePolicy");}groups++;
 }
 public static void main(String[]args){ExileCounterRescueRegression t=new ExileCounterRescueRegression();t.initializeModel();t.baseline=Arrays.asList(args).contains("--baseline");for(String card:List.of("Swan Song","An Offer You Can't Refuse","Counterspell")){t.scenario(card,40);t.scenario(card,3);t.protection(card,true);t.protection(card,false);}System.out.println("Checks passed: "+t.groups);System.exit(0);}
}

