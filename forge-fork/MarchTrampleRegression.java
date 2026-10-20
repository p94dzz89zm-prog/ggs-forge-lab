import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Constructed ordinary-damage trample decisions with real payment/resolution. */
public class MarchTrampleRegression extends AITest {
 int checks;
 void scenario(String profile,int mode) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0),third=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(mode==2?3:mode==6?20:2,null);
  addCard(mode==7?"Mountain":"Island",ai);addCard("Mountain",ai);
  Card valuable=addCard("Balefire Dragon",ai),small=addCard(mode==2?"Runeclaw Bear":"Memnite",mode==3?third:ai);
  Card rat=addCard("Typhoid Rats",opp),trampler=addCard(mode==1?"Stampeding Rhino":mode==4?"Hill Giant":"Colossal Dreadmaw",opp);
  for(Card c:List.of(valuable,small,rat,trampler)){c.setSickness(false);c.setTurnInZone(-1);}
  if(mode==5)trampler.addIntrinsicKeyword("Shroud");
  Combat combat=new Combat(opp);combat.addAttacker(rat,ai);combat.addAttacker(trampler,mode==3?third:ai);
  combat.addBlocker(rat,valuable);combat.addBlocker(trampler,small);combat.setBlocked(rat,true);combat.setBlocked(trampler,true);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));
  Assert.assertNull(CombatUtil.validateBlocks(combat,ai));Assert.assertNull(CombatUtil.validateBlocks(combat,third));
  combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  SpellAbility march=addCardToZone("March of Swirling Mist",ai,ZoneType.Hand).getFirstSpellAbility();march.setActivatingPlayer(ai);
  boolean willing=((PlayerControllerAi)ai.getController()).getAi().canPlaySa(march).willingToPlay();
  if(mode==7){Assert.assertFalse(willing);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),0L);}
  else {
   Assert.assertTrue(willing);Assert.assertEquals(march.getXManaCostPaid(),Integer.valueOf(1));
   Assert.assertTrue(march.getTargets().getTargetCards().contains(mode<3?trampler:valuable),"target priority mode="+mode);
   for(Card c:march.getTargets().getTargetCards())Assert.assertTrue(march.canTarget(c));
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,march,null));g.getStack().resolveStack();
   Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),2L);
   Assert.assertEquals(trampler.isPhasedOut(),mode<3);
   combat.assignCombatDamage(false);combat.dealAssignedDamage();
   Assert.assertEquals(ai.getLife(),mode==2?3:mode==5?-3:mode==6?15:2,"actual damage mode="+mode);
  }
  checks++;System.out.println("PASS March trample "+profile+" mode="+mode);
 }
 public static void main(String[]args){MarchTrampleRegression t=new MarchTrampleRegression();t.initializeModel();for(String p:List.of("BALANCED","ENGINE","ECONOMY"))for(int m=0;m<8;m++)t.scenario(p,m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
