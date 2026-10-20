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

/** Independent constructed checks. Not natural games or whole-game admission. */
public class CounterRescuePaymentRegression extends AITest {
 int checks;
 void drain(Game g) {
  for(int i=0;i<40;i++) {
   g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();
   g.getStack().addAllTriggeredAbilitiesToStack();
   if(g.getStack().isEmpty()) return;
   g.getStack().resolveStack();
  }
  throw new AssertionError("stack did not drain");
 }
 void scenario(int life, boolean guarded) {
  Game g=initAndCreateThreePlayerGame();
  Player ai=g.getPlayers().get(1),attacking=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  System.setProperty("dragonmind.strategyProfile","BALANCED");
  System.setProperty("dragonmind.disableCounterRescuePolicy",Boolean.toString(!guarded));
  for(Player p:g.getPlayers())fillLibrary(p,20);
  ai.setLife(life,null);
  Card body=addCard("Ezio Auditore da Firenze",attacking);
  body.setSickness(false);body.setTurnInZone(-1);
  Card swan=addCardToZone("Swan Song",ai,ZoneType.Hand);Card blue=addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(attacking);combat.addAttacker(body,ai);combat.setBlocked(body,false);
  g.getPhaseHandler().setCombat(combat);
  g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,attacking,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();
  removal.setActivatingPlayer(remover);removal.getTargets().add(body);
  Assert.assertTrue(removal.canTarget(body));
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  SpellAbility counter=swan.getFirstSpellAbility();counter.setActivatingPlayer(ai);
  boolean willing=((PlayerControllerAi)ai.getController()).getAi().canPlaySa(counter).willingToPlay();
  Assert.assertEquals(willing,!guarded,"actual controller choice");
  if(willing) {
   Assert.assertTrue(ComputerUtilCost.canPayCost(counter,ai,false));
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,counter,null));
   Assert.assertTrue(blue.isTapped(),"actual U paid");
  }
  drain(g);
  Assert.assertEquals(body.isInZone(ZoneType.Battlefield),!guarded);
  Assert.assertEquals(combat.isAttacking(body),!guarded);
  Assert.assertEquals(swan.isInZone(ZoneType.Hand),guarded);
  Assert.assertEquals(blue.isTapped(),!guarded);
  combat.assignCombatDamage(false);combat.dealAssignedDamage();
  Assert.assertEquals(ai.getLife(),guarded?life:life-3,"actual combat result");
  System.out.println("PAYMENT_RESULT life="+life+" guarded="+guarded+" after="+ai.getLife());checks++;
 }
 public static void main(String[]args) {
  CounterRescuePaymentRegression t=new CounterRescuePaymentRegression();t.initializeModel();
  for(int life:List.of(1,2,3))for(boolean guarded:List.of(false,true))t.scenario(life,guarded);
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
