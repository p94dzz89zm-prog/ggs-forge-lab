import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.Keyword;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Constructed ordinary blocked-trample rescue with actual priority and costs. */
public class TrampleCounterRescueRegression extends CounterRescuePaymentRegression {
 int groups;
 void scenario(String profile,int life,String counterName,boolean baselineBuild) {scenario(profile,life,counterName,baselineBuild,false);}
 void scenario(String profile,int life,String counterName,boolean baselineBuild,boolean mixedDefender) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);System.clearProperty("dragonmind.disableCounterRescuePolicy");
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(life,null);
  Card target=addCard("Colossal Dreadmaw",enemy),other=addCard("Grizzly Bears",enemy),shield=addCard("Memnite",ai);
  for(Card body:List.of(target,other,shield)){body.setSickness(false);body.setTurnInZone(-1);}
  Card counterCard=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);combat.addAttacker(target,ai);combat.addAttacker(other,ai);if(mixedDefender){Card extra=addCard("Raging Goblin",enemy);extra.setSickness(false);combat.addAttacker(extra,remover);combat.setBlocked(extra,false);}combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(removal.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  if(!baselineBuild)Assert.assertNull(choice,"conserve saving removal in actual priority");
  if(baselineBuild&&profile.equals("BALANCED")&&life==5)Assert.assertNotNull(choice,"original mistake must reproduce");
  boolean countered=choice!=null;
  if(countered){Assert.assertEquals(choice.size(),1);var cast=choice.get(0);Assert.assertEquals(cast.getHostCard(),counterCard);Assert.assertTrue(cast.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(cast,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),countered);Assert.assertEquals(counterCard.isInZone(ZoneType.Hand),!countered);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),countered?(counterName.equals("Counterspell")?2L:1L):0L);
  Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(body->body.isToken()&&body.getName().contains("Treasure")).count(),countered&&counterName.equals("An Offer You Can't Refuse")?2L:0L);
  combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);Assert.assertEquals(ai.getLife(),life-2-(countered?5:0),"actual trample spill5 plus other attacker2");if(!baselineBuild)Assert.assertTrue(ai.getLife()>0);
  System.out.println("TRAMPLE_COUNTER profile="+profile+" life="+life+" card="+counterName+" mixed="+mixedDefender+" countered="+countered+" after="+ai.getLife());groups++;
 }
 void boundary(String counterName,int mode) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");System.clearProperty("dragonmind.disableCounterRescuePolicy");for(Player p:g.getPlayers())fillLibrary(p,12);ai.setLife(mode==0?8:mode==5?6:5,null);
  Card target=addCard(mode==1?"Hill Giant":"Colossal Dreadmaw",enemy),other=addCard(mode==5?"Craw Wurm":"Grizzly Bears",enemy),shield=addCard(mode==4?"White Knight":"Memnite",mode==2?remover:ai);for(Card body:List.of(target,other,shield))body.setSickness(false);
  if(mode==3)addCard("Chariot of Victory",enemy).attachToEntity(target,null);g.getAction().checkStateEffects(true);
  if(mode==3)Assert.assertTrue(target.hasKeyword(Keyword.FIRST_STRIKE));
  if(mode==4)Assert.assertTrue(shield.hasKeyword(Keyword.FIRST_STRIKE));
  Combat combat=new Combat(enemy);combat.addAttacker(target,mode==2?remover:ai);combat.addAttacker(other,ai);combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));Assert.assertNull(CombatUtil.validateBlocks(combat,remover));
  Card counterCard=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  var removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));var counter=counterCard.getFirstSpellAbility();counter.setActivatingPlayer(ai);
  Assert.assertFalse(GgsCounterRescuePolicy.rejectLethalRescueCounter(ai,counter),"outside ordinary rescuing boundary mode="+mode);
  var pilot=((PlayerControllerAi)ai.getController()).getAi();var decision=pilot.canPlaySa(counter);System.setProperty("dragonmind.disableCounterRescuePolicy","true");Assert.assertEquals(pilot.canPlaySa(counter),decision);System.clearProperty("dragonmind.disableCounterRescuePolicy");System.out.println("TRAMPLE_BOUNDARY card="+counterName+" mode="+mode+" unchanged");groups++;
 }
 public static void main(String[]args){TrampleCounterRescueRegression t=new TrampleCounterRescueRegression();t.initializeModel();boolean baseline=Arrays.asList(args).contains("--baseline");for(String counter:List.of("Swan Song","An Offer You Can't Refuse","Counterspell")){for(String profile:List.of("BALANCED","ENGINE","ECONOMY"))for(int life:List.of(3,4,5,6,7))t.scenario(profile,life,counter,baseline);t.scenario("BALANCED",6,counter,baseline,true);for(int mode=0;mode<6;mode++)t.boundary(counter,mode);}System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
