import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Constructed decisions, with actual removal/counter costs and resolution. */
public class CounterRescueRegression extends AITest {
 int checks;
 void drain(Game g){for(int i=0;i<40;i++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new AssertionError("stack did not drain");}
 void scenario(String profile,int mode){
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),attacking=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",mode==6?"disabled":ai.getName());System.clearProperty("dragonmind.disableCounterRescuePolicy");System.setProperty("dragonmind.strategyProfile",profile);
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(mode==1?1:mode==3?5:mode==4?10:3,null);
  Card body=addCard(mode==2?"Hill Giant":mode==3?"Craw Wurm":"Ezio Auditore da Firenze",attacking);body.setSickness(false);body.setTurnInZone(-1);
  Card swan=addCardToZone(mode==7?"Counterspell":"Swan Song",ai,ZoneType.Hand);addCard("Island",ai);if(mode==7)addCard("Island",ai);
  for(String n:mode==3?List.of("Swamp","Swamp"):List.of("Plains","Swamp","Swamp"))addCard(n,remover);
  Combat combat=new Combat(attacking);combat.addAttacker(body,mode==5?remover:ai);combat.setBlocked(body,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,attacking,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));
  SpellAbility removal=addCardToZone(mode==3?"Doom Blade":"Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(body);
  Assert.assertTrue(removal.canTarget(body));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),mode==3?2L:3L);
  SpellAbility counter=swan.getFirstSpellAbility();counter.setActivatingPlayer(ai);
  Assert.assertEquals(GgsCounterRescuePolicy.rejectLethalRescueCounter(ai,counter),mode<4,"guard boundary "+mode);
  AiController pilot=((PlayerControllerAi)ai.getController()).getAi();AiPlayDecision decision=pilot.canPlaySa(counter);
  if(mode<4){
   Assert.assertFalse(decision.willingToPlay());
   System.setProperty("dragonmind.disableCounterRescuePolicy","true");boolean stockWouldCounter=pilot.canPlaySa(counter).willingToPlay();System.clearProperty("dragonmind.disableCounterRescuePolicy");
   // The original Mortify reproduction must distinguish the policies. Stock
   // can already decline cheaper removal in variants; record that parity
   // rather than assuming every profile misplays every different spell.
   if(mode==0)Assert.assertTrue(stockWouldCounter,"original Mortify mistake reproduced");
   System.out.println("STOCK_WOULD_COUNTER="+stockWouldCounter+" profile="+profile+" mode="+mode);
   Assert.assertTrue(ComputerUtilCost.canPayCost(counter,ai,false),"available counter deliberately conserved");
   drain(g);Assert.assertFalse(body.isInZone(ZoneType.Battlefield));Assert.assertFalse(combat.isAttacking(body));
   combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(ai.getLife(),mode==1?1:mode==3?5:3);
   Assert.assertTrue(swan.isInZone(ZoneType.Hand));Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),0L);
  }else{
   System.setProperty("dragonmind.disableCounterRescuePolicy","true");Assert.assertEquals(pilot.canPlaySa(counter),decision,"unchanged stock boundary "+mode);System.clearProperty("dragonmind.disableCounterRescuePolicy");
  }
  checks++;System.out.println("PASS counter rescue "+profile+" mode="+mode);
 }
 public static void main(String[]args){CounterRescueRegression t=new CounterRescueRegression();t.initializeModel();for(String p:List.of("BALANCED","ENGINE","ECONOMY"))for(int m=0;m<8;m++)t.scenario(p,m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
