import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

public class CombatRecoveryRegression extends AITest {
 int checks;void pass(String n){checks++;System.out.println("PASS "+n);}
 void enabled(Player ai){System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.clearProperty("dragonmind.disableSneakPolicy");System.clearProperty("dragonmind.disableFreshAttackPolicy");}
 void drain(Game g){for(int i=0;i<40;i++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new AssertionError("Stack did not drain");}
 void cast(boolean sneak) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enabled(ai);
  Card ggs=addCard("Goro-Goro and Satoru",ai);ggs.setCommander(true);
  addCard("Satoru Umezawa",ai);addCard("Satoru, the Infiltrator",ai);
  Card old=addCard("Changeling Outcast",ai);old.setSickness(false);old.setTurnInZone(-1);
  if(sneak)addCard("Ninja Teen",ai).setClassLevel(3);
  Card incoming=addCardToZone("Nezumi Prowler",ai,sneak?ZoneType.Graveyard:ZoneType.Hand);
  for(int i=0;i<(sneak?4:2);i++)addCard("Swamp",ai);
  fillLibrary(ai,20);fillLibrary(opp,20);g.getAction().checkStateEffects(true);g.getTriggerHandler().resetActiveTriggers();
  Combat combat=new Combat(ai);combat.addAttacker(old,opp);combat.setBlocked(old,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  SpellAbility sa=ComputerUtilAbility.getSpellAbilities(new CardCollection(incoming),ai).stream()
    .filter(s->sneak?s.isSneak():s.isNinjutsu()&&s.getPayCosts().getTotalMana().getCMC()==2).findFirst().orElseThrow();sa.setActivatingPlayer(ai);
  Assert.assertTrue(((PlayerControllerAi)ai.getController()).getAi().canPlaySa(sa).willingToPlay());pass((sneak?"Sneak":"Ninjutsu")+" willing");
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));drain(g);
  Card actual=ai.getCreaturesInPlay().stream().filter(c->c.getName().equals("Nezumi Prowler")).findFirst().orElseThrow();
  Assert.assertTrue(old.isInZone(ZoneType.Hand));Assert.assertTrue(ggs.isInZone(ZoneType.Battlefield));pass("pays return without bouncing commander");
  Assert.assertTrue(combat.isAttacking(actual));Assert.assertTrue(actual.enteredThisTurn());pass("fresh attacker actually enters combat");
  Assert.assertTrue(actual.hasKeyword(Keyword.LIFELINK));Assert.assertTrue(actual.hasKeyword(Keyword.DEATHTOUCH));pass("Prowler actual ETB resolution");
  Assert.assertEquals(ai.getCardsIn(ZoneType.Hand).size(),sneak?1:3);pass("both Satoru reward distinction "+sneak);
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),sneak?4L:2L);pass("real casting/activation payment");
 }
 void fresh(int mode) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enabled(ai);
  if(mode!=6)addCard("Goro-Goro and Satoru",ai);
  Card ground=addCard("Runeclaw Bear",ai);ground.setSickness(false);ground.setTurnInZone(-1);
  Card fresh=addCard("Thousand-Faced Shadow",ai);fresh.setSickness(false);fresh.setTurnInZone(g.getPhaseHandler().getTurn());
  Combat combat=new Combat(ai);combat.addAttacker(ground,opp);
  if(mode==1)combat.addAttacker(fresh,opp);
  if(mode==2){ground.addIntrinsicKeyword("Flying");ground.setTurnInZone(g.getPhaseHandler().getTurn());}
  if(mode==3)addCard("Birds of Paradise",opp);
  if(mode==4)addCard("Ghostly Prison",opp);
  if(mode==5)System.setProperty("dragonmind.disableFreshAttackPolicy","true");
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);
  fresh.setTurnInZone(g.getPhaseHandler().getTurn());
  if(mode==2)ground.setTurnInZone(g.getPhaseHandler().getTurn());
  GgsFreshAttackPolicy.supplement(ai,combat);
  Assert.assertEquals(combat.isAttacking(fresh),mode==0||mode==1,"fresh attack mode "+mode);
  Assert.assertTrue(combat.isAttacking(ground));Assert.assertTrue(CombatUtil.validateAttackers(combat));pass("fresh attack legal and scope "+mode);
 }
 void profile(String profile) {
  System.setProperty("dragonmind.strategyProfile",profile);
  Assert.assertEquals(AdaptiveStrategy.current().name(),profile);
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1);enabled(ai);
  addCardToZone("Goro-Goro and Satoru",ai,ZoneType.Command).setCommander(true);
  for(String n:List.of("Island","Mountain","Swamp","Command Tower","Grim Hireling","Balefire Dragon","Fierce Guardianship"))addCardToZone(n,ai,ZoneType.Hand);
  Assert.assertEquals(GgsRecoveryPolicy.rejectSlowSeven(ai,0),profile.equals("BALANCED"));pass("profile changes actual opening preference "+profile);
 }
 public static void main(String[]args){CombatRecoveryRegression t=new CombatRecoveryRegression();t.initializeModel();t.cast(false);t.cast(true);for(int i=0;i<7;i++)t.fresh(i);for(String p:List.of("BALANCED","ENGINE","ECONOMY"))t.profile(p);System.clearProperty("dragonmind.strategyProfile");System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
