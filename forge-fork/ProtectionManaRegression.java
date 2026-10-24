import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.ability.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Constructed public-threat decisions, never natural games. */
public class ProtectionManaRegression extends AITest {
 int checks;
 record Board(Game g,Player p,Player enemy,Card commander,Card removal,Card march,SpellAbility haste){}
 Board board(String threat,int mana,boolean tapped,boolean sick) {
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player p=g.getPlayers().get(1),enemy=g.getPlayers().get(0);System.setProperty("forge.ai.ggsPilotPlayer",p.getName());
  for(Player s:g.getPlayers())fillLibrary(s,12);
  Card commander=addCard("Goro-Goro and Satoru",p);commander.setCommander(true);p.addCommander(commander);p.createCommanderEffect();commander.setSickness(false);commander.setTurnInZone(-1);
  Card fresh=addCard("Kari Zev, Skyship Raider",p);fresh.setSickness(true);fresh.setTurnInZone(5);
  Card removal=addCard(threat,enemy);removal.setSickness(sick);removal.setTapped(tapped);removal.setTurnInZone(sick?5:-1);
  Card march=addCardToZone("March of Swirling Mist",p,ZoneType.Hand);
  for(int i=0;i<mana;i++)addCard(i==0?"Island":"Mountain",p);
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,5);
  SpellAbility haste=commander.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.PumpAll).findFirst().orElseThrow();haste.setActivatingPlayer(p);
  return new Board(g,p,enemy,commander,removal,march,haste);
 }
 static SpellAbility removal(Board b) {
  var sa=b.removal().getSpellAbilities().stream().filter(x->x.getApi()==ApiType.Destroy).findFirst().orElseThrow();sa.setActivatingPlayer(b.enemy());sa.resetTargets();sa.getTargets().add(b.commander());return sa;
 }
 static SpellAbility protection(Board b) {
  var sa=b.march().getFirstSpellAbility();sa.setActivatingPlayer(b.p());sa.setXManaCostPaid(1);sa.resetTargets();sa.getTargets().add(b.commander());return sa;
 }
 static void fire(Board b,boolean protect) {
  var kill=removal(b);Assert.assertTrue(kill.canPlay(),"actual opponent instant-speed ability timing");Assert.assertTrue(kill.canTarget(b.commander()));Assert.assertTrue(ComputerUtilCost.canPayCost(kill,b.enemy(),false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.enemy(),kill,null));Assert.assertTrue(b.removal().isTapped());
  if(protect){var top=b.g().getStack().peekAbility();System.out.println("STACK TARGETS "+top.getTargets()+" orig="+(top.getOriginalAbility()==null?"null":top.getOriginalAbility().getTargets())+" threatened="+ComputerUtil.predictThreatenedObjects(b.p(),null,true));var probe=protection(b);System.out.println("PROTECTION AI "+((PlayerControllerAi)b.p().getController()).getAi().canPlaySa(probe)+" targets="+probe.getTargets()+" x="+probe.getXManaCostPaid()+" canPlay="+probe.canPlay()+" stack="+b.g().getStack().peekAbility());var picked=((PlayerControllerAi)b.p().getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(picked,"pilot chooses protection in real priority selection");Assert.assertEquals(picked.size(),1);var save=picked.get(0);Assert.assertEquals(save.getHostCard().getName(),"March of Swirling Mist");Assert.assertTrue(save.getTargets().getTargetCards().contains(b.commander()),"pilot targets the threatened GGS");Assert.assertTrue(save.canPlay());Assert.assertTrue(save.canTarget(b.commander()));Assert.assertTrue(ComputerUtilCost.canPayCost(save,b.p(),false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),save,null));}
  LinePlannerRegression.drain(b.g());
 }
 void demonstrate(boolean protect) {
  Board b=board("Avatar of Woe",2,false,false);
  if(!protect){Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),b.haste(),null));LinePlannerRegression.drain(b.g());Assert.assertFalse(ComputerUtilCost.canPayCost(protection(b),b.p(),false));}
  fire(b,protect);
  Assert.assertEquals(b.g().getCardsIncludePhasingIn(ZoneType.Battlefield).anyMatch(c->c.getId()==b.commander().getId()),protect);
  if(protect){Assert.assertTrue(b.commander().isPhasedOut());Assert.assertEquals((int)b.p().getLandsInPlay().stream().filter(Card::isTapped).count(),2);}
  System.out.println("RESPONSE protect="+protect+" commander_retained="+protect);checks++;
 }
 void choice(boolean expectHold) {
  System.setProperty("dragonmind.disableProtectionReserve",Boolean.toString(!expectHold));
  Board b=board("Avatar of Woe",2,false,false);System.setProperty("dragonmind.linePlanner","true");System.setProperty("dragonmind.linePlannerMillis","60000");String before=PlannerSnapshot.forPlayer(b.p()).toString();
  var chosen=GgsLinePlanner.select(b.p(),List.of(b.haste()));System.out.println("RESERVE CHOICE "+chosen);Assert.assertEquals(PlannerSnapshot.forPlayer(b.p()).toString(),before);
  if(expectHold){Assert.assertNull(chosen,"keep actual March mana against ready public removal");fire(b,true);Assert.assertTrue(b.commander().isPhasedOut());}
  else{Assert.assertNotNull(chosen);Assert.assertEquals(chosen.get(0).getApi(),ApiType.PumpAll);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),chosen.get(0),null));LinePlannerRegression.drain(b.g());fire(b,false);Assert.assertFalse(b.g().getCardsIncludePhasingIn(ZoneType.Battlefield).anyMatch(c->c.getId()==b.commander().getId()));}
  System.clearProperty("dragonmind.linePlanner");System.clearProperty("dragonmind.linePlannerMillis");System.clearProperty("dragonmind.disableProtectionReserve");checks++;
 }
 void control(int mode) {
  Board b=board("Avatar of Woe",mode==2?4:mode==6?3:2,mode==0,mode==1);
  if(mode==3)b.g().getAction().moveTo(ZoneType.Exile,b.march(),null,Map.of());
  if(mode==4){addCard("Avacyn, Angel of Hope",b.p());b.g().getAction().checkStateEffects(true);Assert.assertTrue(b.commander().hasKeyword(forge.game.keyword.Keyword.INDESTRUCTIBLE));}
  if(mode==6)addCardToZone("Opt",b.p(),ZoneType.Hand);
  System.setProperty("dragonmind.linePlanner","true");System.setProperty("dragonmind.linePlannerMillis","60000");System.setProperty("dragonmind.disableProtectionReserve",Boolean.toString(mode==5));
  String before=PlannerSnapshot.forPlayer(b.p()).toString();var rng=forge.util.MyRandom.getRandom();
  var chosen=GgsLinePlanner.select(b.p(),List.of(b.haste()));Assert.assertNotNull(chosen,"no unnecessary reserve mode="+mode);Assert.assertEquals(PlannerSnapshot.forPlayer(b.p()).toString(),before);Assert.assertSame(forge.util.MyRandom.getRandom(),rng);
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),chosen.get(0),null));LinePlannerRegression.drain(b.g());
  if(mode==2){Assert.assertTrue(ComputerUtilCost.canPayCost(protection(b),b.p(),false),"enough colored mana remains after actual haste payment");fire(b,true);Assert.assertTrue(b.commander().isPhasedOut());}
  if(mode==4){fire(b,false);Assert.assertTrue(b.g().getCardsIncludePhasingIn(ZoneType.Battlefield).anyMatch(c->c.getId()==b.commander().getId()));}
  if(mode==5){fire(b,false);Assert.assertFalse(b.g().getCardsIncludePhasingIn(ZoneType.Battlefield).anyMatch(c->c.getId()==b.commander().getId()));}
  System.clearProperty("dragonmind.linePlanner");System.clearProperty("dragonmind.linePlannerMillis");System.clearProperty("dragonmind.disableProtectionReserve");System.out.println("CONTROL "+mode+" action retained");checks++;
 }
 public static void main(String[]args){ProtectionManaRegression t=new ProtectionManaRegression();t.initializeModel();t.demonstrate(false);t.demonstrate(true);t.choice(args.length==0||!args[0].equals("--baseline"));for(int m=0;m<7;m++)t.control(m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
