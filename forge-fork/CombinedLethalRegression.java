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

/** Constructed decisions; never counted as natural pod games. */
public class CombinedLethalRegression extends AITest {
 int checks;
 void scenario(String profile,int mode) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0),third=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);
  Card commander=addCard("Goro-Goro and Satoru",ai);commander.setCommander(true);
  Card old=addCard("Colossal Dreadmaw",ai);
  Card incoming=addCardToZone("Nezumi Prowler",ai,ZoneType.Hand);
  for(int i=0;i<2;i++)addCard("Swamp",ai);for(Player p:g.getPlayers())fillLibrary(p,20);
  g.getAction().checkStateEffects(true);opp.setLife(mode==1?8:mode==2?10:9,null);
  Combat combat=new Combat(ai);
  for(Card c:List.of(old,commander)){c.setSickness(false);c.setTurnInZone(-1);combat.addAttacker(c,c==commander&&mode==3?third:opp);combat.setBlocked(c,false);}
  if(mode==4)old.addIntrinsicKeyword("First strike");
  if(mode==5)commander.addIntrinsicKeyword("First strike");
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(mode>=4?PhaseType.COMBAT_FIRST_STRIKE_DAMAGE:PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  SpellAbility sa=ComputerUtilAbility.getSpellAbilities(new CardCollection(incoming),ai).stream().filter(SpellAbility::isNinjutsu).findFirst().orElseThrow();sa.setActivatingPlayer(ai);
  Assert.assertTrue(ComputerUtilCost.canPayCost(sa,ai,false),"payable alternative");
  var plan=GgsNinjutsuPolicy.choose(ai,sa,combat.getUnblockedAttackers());
  if(mode<2){
   Assert.assertNull(plan,"preserve combined lethal "+profile+" mode="+mode);
   Assert.assertFalse(((PlayerControllerAi)ai.getController()).getAi().canPlaySa(sa).willingToPlay());
   Assert.assertTrue(combat.isAttacking(old));Assert.assertTrue(combat.isAttacking(commander));
   Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),0L);
   combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertTrue(opp.getLife()<=0,"actual combined lethal damage");
  }else{
   Assert.assertNotNull(plan,"no false lethal veto "+profile+" mode="+mode);
   Assert.assertEquals(plan.returned(),old);
   if(mode==2&&profile.equals("BALANCED")){
    Assert.assertTrue(((PlayerControllerAi)ai.getController()).getAi().canPlaySa(sa).willingToPlay());
    Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));
    for(int i=0;i<30;i++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())break;g.getStack().resolveStack();}
    Assert.assertTrue(g.getStack().isEmpty());Assert.assertTrue(old.isInZone(ZoneType.Hand));
    Assert.assertTrue(ai.getCreaturesInPlay().stream().anyMatch(c->c.getName().equals("Nezumi Prowler")&&combat.isAttacking(c)));
    Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),2L);
    combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(opp.getLife(),4,"actual post-swap combat damage");
   }
  }
  System.out.println("PASS combined lethal "+profile+" mode="+mode);checks++;
 }
 public static void main(String[] args){CombinedLethalRegression t=new CombinedLethalRegression();t.initializeModel();for(String p:List.of("BALANCED","ENGINE","ECONOMY"))for(int m=0;m<6;m++)t.scenario(p,m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
