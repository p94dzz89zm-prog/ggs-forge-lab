import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.ability.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

public class PilotRecoveryRegression extends AITest {
 int checks;
 void pass(String s) { checks++; System.out.println("PASS "+s); }
 AiController pilot(Player ai) { return ((PlayerControllerAi)ai.getController()).getAi(); }
 void enable(Player ai) { System.setProperty("forge.ai.ggsPilotPlayer",ai.getName()); System.clearProperty("dragonmind.disableRecoveryPolicy"); }
 void opening(int mode) {
  Game g=initAndCreateGame(); Player ai=g.getPlayers().get(1); enable(ai);
  if(mode!=10)addCardToZone("Goro-Goro and Satoru",ai,ZoneType.Command).setCommander(true);
  for(int i=0;i<10;i++)addCardToZone("Island",ai,ZoneType.Library);fillLibrary(ai,20);
  List<String> hand=new ArrayList<>(List.of("Undercity Sewers","Scalding Tarn","Command Tower","Fierce Guardianship","Steam Vents","Fell the Profane","Grim Hireling"));
  String[] early={"Phoenix Chick","Arcane Signet","Urabrask's Forge","Demonic Tutor","Swan Song","Faerie Seer","Moon-Circuit Hacker"};
  if(mode>=1&&mode<=7)hand.set(6,early[mode-1]);
  if(mode==8)hand.remove(0);
  if(mode==11)hand.set(0,"Balefire Dragon");
  for(String n:hand)addCardToZone(n,ai,ZoneType.Hand);
  if(mode==12)System.setProperty("dragonmind.disableRecoveryPolicy","true");
  int returning=mode==9?1:0;
  boolean expected=mode==0;
  Assert.assertEquals(GgsRecoveryPolicy.rejectSlowSeven(ai,returning),expected,"opening mode "+mode);
  if(expected)Assert.assertTrue(ComputerUtil.wantMulligan(ai,returning));
  pass("opening scope "+mode);
 }
 void prowler(int mode) {
  Game g=initAndCreateGame(); Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enable(ai);
  Card commander=addCard("Goro-Goro and Satoru",ai);
  Card incoming=addCard("Nezumi Prowler",ai);incoming.setSickness(false);
  SpellAbility pump=AbilityFactory.getAbility(incoming.getSVar("TrigPump"),incoming);pump.setActivatingPlayer(ai);
  Combat combat=new Combat(ai);combat.addAttacker(incoming,opp);combat.setBlocked(incoming,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  Card expected=incoming;
  switch(mode) {
   case 1: incoming.addIntrinsicKeyword("Lifelink");expected=null;break;
   case 2: combat.setBlocked(incoming,true);expected=null;break;
   case 3: incoming.addIntrinsicKeyword("Shroud");expected=null;break;
   case 4: g.getPhaseHandler().devModeSet(PhaseType.MAIN2,ai,false);expected=null;break;
   case 5: g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);expected=null;break;
   case 6: System.setProperty("dragonmind.disableRecoveryPolicy","true");expected=null;break;
   case 7: incoming.addIntrinsicKeyword("First strike");g.getPhaseHandler().devModeSet(PhaseType.COMBAT_FIRST_STRIKE_DAMAGE,ai,false);expected=null;break;
   case 8: incoming.addIntrinsicKeyword("First strike");incoming.addIntrinsicKeyword("Double strike");g.getPhaseHandler().devModeSet(PhaseType.COMBAT_FIRST_STRIKE_DAMAGE,ai,false);break;
   case 9: Card big=addCard("Colossal Dreadmaw",ai);big.setSickness(false);combat.addAttacker(big,opp);combat.setBlocked(big,false);expected=big;break;
   case 10: combat.removeFromCombat(incoming);expected=null;break;
   case 11: incoming.setController(opp,0);expected=null;break;
   case 12: System.clearProperty("forge.ai.ggsPilotPlayer");expected=null;break;
   case 13: incoming.addIntrinsicKeyword("Deathtouch");break;
  }
  Assert.assertEquals(GgsRecoveryPolicy.prowlerTarget(ai,pump),expected,"Prowler mode "+mode);
  if(expected!=null) {
   Assert.assertTrue(pilot(ai).doTrigger(pump,true));
   Assert.assertEquals(pump.getTargets().getTargetCards().get(0),expected);
   Assert.assertFalse(pump.getTargets().getTargetCards().contains(commander));
   AbilityUtils.resolve(pump);
   Assert.assertTrue(expected.hasKeyword(Keyword.LIFELINK));Assert.assertTrue(expected.hasKeyword(Keyword.DEATHTOUCH));
  }
  pass("actual Prowler target/resolution "+mode);
 }
 void assault(int mode) throws Exception {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enable(ai);
  fillLibrary(ai,10);fillLibrary(opp,10);
  Card body=addCard(mode==4?"Runeclaw Bear":"Changeling Outcast",ai);body.setSickness(mode==7);
  body.setTurnInZone(-1);
  if(mode!=1)addCard("Sword of Feast and Famine",ai).attachToEntity(body,null);
  Card assault=addCard("Aggravated Assault",ai);
  for(int i=0;i<(mode==3?4:5);i++)addCard(mode==2?"Island":"Mountain",ai);
  if(mode==4)addCard("Wurmcoil Engine",opp);
  if(mode==5)addCard("Ghostly Prison",opp);
  if(mode==8)System.setProperty("dragonmind.disableRecoveryPolicy","true");
  g.getAction().checkStateEffects(true);
  g.getPhaseHandler().devModeSet(mode==6?PhaseType.MAIN1:PhaseType.MAIN2,ai,false);
  SpellAbility sa=assault.getSpellAbilities().stream().filter(x->x.getApi()==ApiType.UntapAll).findFirst().orElseThrow();sa.setActivatingPlayer(ai);
  var method=AiController.class.getDeclaredMethod("canPlayAndPayFor",SpellAbility.class);method.setAccessible(true);
  Object choice=method.invoke(pilot(ai),sa);
  if(mode==0) {
   Assert.assertEquals(choice,AiPlayDecision.WillPlay);
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));g.getStack().resolveStack();
   Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),5L);
   Assert.assertFalse(body.isTapped());
   Assert.assertTrue(g.getPhaseHandler().hasExtraPhaseAfter(PhaseType.MAIN2,PhaseType.COMBAT_BEGIN));
  } else {
   System.setProperty("dragonmind.disableRecoveryPolicy","true");
   Assert.assertEquals(choice,method.invoke(pilot(ai),sa),"stock boundary "+mode);
   if(mode==2||mode==3)Assert.assertFalse(ComputerUtilCost.canPayCost(sa,ai,false));
  }
  pass("Assault actual decision/payment/extra phase "+mode);
 }
 public static void main(String[] args) throws Exception {
  PilotRecoveryRegression t=new PilotRecoveryRegression();t.initializeModel();
  for(int i=0;i<13;i++)t.opening(i);
  for(int i=0;i<14;i++)t.prowler(i);
  for(int i=0;i<9;i++)t.assault(i);
  for(int seed=0;seed<16;seed++){forge.util.MyRandom.setRandom(new Random(seed));t.prowler(0);}
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
