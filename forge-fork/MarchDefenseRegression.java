import forge.ai.*;
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

/** Constructed March decisions with actual costs, targeting and damage. */
public class MarchDefenseRegression extends AITest {
 int checks;
 void scenario(String profile,int mode) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0),third=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",mode==8?"disabled":ai.getName());System.setProperty("dragonmind.strategyProfile",profile);
  for(Player p:g.getPlayers())fillLibrary(p,20);
  ai.setLife(mode==7?20:mode==2?5:2,null);
  addCard(mode==4?"Mountain":"Island",ai);addCard("Mountain",ai);if(mode==5)addCard("Mountain",ai);
  Card valuable=addCard("Balefire Dragon",ai),rat=addCard("Typhoid Rats",opp),lethal=addCard(mode==1||mode==2?"Colossal Dreadmaw":"Centaur Courser",opp);
  for(Card c:List.of(valuable,rat,lethal)){c.setSickness(false);c.setTurnInZone(-1);}
  Combat combat=new Combat(opp);combat.addAttacker(rat,ai);combat.addAttacker(lethal,ai);combat.addBlocker(rat,valuable);combat.setBlocked(rat,true);combat.setBlocked(lethal,false);
  if(mode==2){Card other=addCard("Centaur Courser",opp);other.setSickness(false);combat.addAttacker(other,ai);combat.setBlocked(other,false);}
  if(mode==3){Card other=addCard("Kozilek, Butcher of Truth",opp);other.setSickness(false);combat.addAttacker(other,third);combat.setBlocked(other,false);}
  if(mode==6)lethal.addIntrinsicKeyword("Shroud");
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);
  SpellAbility march=addCardToZone("March of Swirling Mist",ai,ZoneType.Hand).getFirstSpellAbility();march.setActivatingPlayer(ai);
  Assert.assertTrue(CombatUtil.validateAttackers(combat),"legal attack assignment");
  boolean willing=((PlayerControllerAi)ai.getController()).getAi().canPlaySa(march).willingToPlay();
  if(mode==4||mode==8){
   Assert.assertFalse(willing,"color/opt-in boundary");Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),0L);
  }else{
   Assert.assertTrue(willing);
   if(mode==7||mode==6)Assert.assertTrue(march.getTargets().getTargetCards().contains(valuable));
   else Assert.assertTrue(march.getTargets().getTargetCards().contains(lethal),"prevent lethal before saving blocker");
   int x=march.getXManaCostPaid();Assert.assertEquals(x,mode==5?2:1);
   for(Card c:march.getTargets().getTargetCards())Assert.assertTrue(march.canTarget(c));
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,march,null),"actual legal payment");g.getStack().resolveStack();
   Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),(long)x+1);
   Assert.assertEquals(lethal.isPhasedOut(),mode!=6&&mode!=7);
   combat.assignCombatDamage(false);combat.dealAssignedDamage();
   Assert.assertEquals(ai.getLife(),mode==6?-1:mode==7?17:mode==2?2:2,"actual resulting life");
  }
  System.out.println("PASS March defense "+profile+" mode="+mode);checks++;
 }
 public static void main(String[]args){MarchDefenseRegression t=new MarchDefenseRegression();t.initializeModel();for(String p:List.of("BALANCED","ENGINE","ECONOMY"))for(int m=0;m<9;m++)t.scenario(p,m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
