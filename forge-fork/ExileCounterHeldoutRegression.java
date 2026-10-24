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
public class ExileCounterHeldoutRegression extends CounterRescuePaymentRegression {
 int groups;
 void scenario(String counterName,boolean baseline,int variant) {
  int mode=0;boolean manualPass=false;
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");
  for(Player p:g.getPlayers())fillLibrary(p,20);int life=mode==1?7:5;ai.setLife(life,null);remover.setLife(40,null);
  Card target=addCard(variant==0?"Stampeding Rhino":"Darksteel Colossus",enemy),other=addCard(variant==0?"Grizzly Bears":"Raging Goblin",enemy),shield=addCard(variant==0?"Memnite":"Runeclaw Bear",ai);
  for(Card body:List.of(target,other,shield)){body.setSickness(false);body.setTurnInZone(-1);}
  g.getAction().checkStateEffects(true);

  int spill=target.getNetCombatDamage()-shield.getLethalDamage();Assert.assertTrue(spill>0);life=spill+other.getNetCombatDamage();ai.setLife(life,null);if(variant==1)Assert.assertTrue(target.hasKeyword(Keyword.INDESTRUCTIBLE));
  Card counter=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);combat.addAttacker(target,ai);combat.addAttacker(other,ai);combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  var removal=addCardToZone("Anguished Unmaking",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canPlay());Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();boolean countered=!manualPass&&choice!=null;
  Assert.assertEquals(choice!=null,baseline,"frozen actual exile rescue choice");
  if(countered){var cast=choice.get(0);Assert.assertEquals(cast.getHostCard(),counter);Assert.assertTrue(cast.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(cast,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),countered);
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),countered?(counterName.equals("Counterspell")?2L:1L):0L);
  Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(b->b.isToken()&&b.getName().contains("Treasure")).count(),countered&&counterName.equals("An Offer You Can't Refuse")?2L:0L);
  combat.assignCombatDamage(true);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);drain(g);
  if(ai.getLife()>0){combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);}
  Assert.assertEquals(ai.getLife(),countered?0:life-other.getNetCombatDamage());Assert.assertEquals(target.isInZone(ZoneType.Exile),!countered);Assert.assertEquals(ai.getLife()>0,!baseline);groups++;Assert.assertEquals(remover.getLife(),countered?40:37);
  System.out.println("HELDOUT_EXILE variant="+variant+" mode="+mode+" card="+counterName+" manualPass="+manualPass+" automaticChoice="+(choice!=null)+" countered="+countered+" finalLife="+ai.getLife());
 }
 public static void main(String[]args){Assert.assertTrue(Arrays.asList(args).contains("--purpose")&&Arrays.asList(args).contains("heldout"));ExileCounterHeldoutRegression t=new ExileCounterHeldoutRegression();t.initializeModel();boolean baseline=Arrays.asList(args).contains("--baseline");for(String card:List.of("Swan Song","An Offer You Can't Refuse","Counterspell"))for(int variant=0;variant<2;variant++)t.scenario(card,baseline,variant);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}

