import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Constructed engine executions, not natural games or training feedback. */
public class LinePlannerRegression extends AITest {
 int checks;
 Game position(int lands,boolean blocker) {
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;
  Player p=g.getPlayers().get(1);System.setProperty("forge.ai.ggsPilotPlayer",p.getName());
  for(Player s:g.getPlayers())fillLibrary(s,12);
  Card commander=addCard("Goro-Goro and Satoru",p);commander.setCommander(true);commander.setSickness(false);commander.setTurnInZone(-1);
  addCardToZone("Kari Zev, Skyship Raider",p,ZoneType.Hand);
  for(int i=0;i<lands;i++)addCard(i==0?"Island":"Mountain",p);
  if(blocker)for(Player s:g.getPlayers())if(s!=p)for(int i=0;i<3;i++){Card c=addCard("Colossal Dreadmaw",s);c.setSickness(false);c.setTurnInZone(-1);}
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,5);return g;
 }
 void reviewCase(int lands,boolean blocker) {
  Game g=position(lands,blocker);Player p=g.getPlayers().get(1);String before=PlannerSnapshot.forPlayer(p).toString();
  var r=GgsLinePlanner.review(p,60000);System.out.println("REVIEW lands="+lands+" blocker="+blocker+" "+r);
  Assert.assertEquals(r.status(),"complete-bounded");Assert.assertEquals(PlannerSnapshot.forPlayer(p).toString(),before);
  Assert.assertEquals(r.lines().get(0).creatures(),1,"old commander must not make a Dragon");
  if(lands==4&&!blocker){
   Assert.assertEquals(r.chosen().size(),2,"see cast then haste beyond single action");
   Assert.assertTrue(r.chosen().get(0).label().startsWith("Kari Zev"));
   Assert.assertTrue(r.chosen().get(1).label().startsWith("Goro-Goro"));
   Assert.assertTrue(r.lines().stream().anyMatch(l->l.actions().size()==2&&l.creatures()>=4),"actual combat creates token board");
  }
  if(lands==2)Assert.assertFalse(r.lines().stream().anyMatch(l->l.actions().size()==2),"no unpaid haste");
  if(blocker)Assert.assertTrue(r.chosen().size()<2,"blocked line changes decision");
  checks++;
 }
 void boundaries() {
  Game g=position(4,false);Player p=g.getPlayers().get(1);
  Assert.assertTrue(GgsLinePlanner.review(p,0).status().contains("deadline"));checks++;
  g.EXPERIMENTAL_RESTORE_SNAPSHOT=true;Assert.assertEquals(GgsLinePlanner.review(p,1000).status(),"unsupported-position");g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;checks++;
  g.getPhaseHandler().devModeSet(PhaseType.UPKEEP,p,false,5);Assert.assertFalse(GgsLinePlanner.eligible(p));checks++;
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,g.getPlayers().get(0),false,5);Assert.assertFalse(GgsLinePlanner.eligible(p));checks++;
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,5);
  Card facedown=addCard("Colossal Dreadmaw",p);facedown.turnFaceDown(true);Assert.assertFalse(GgsLinePlanner.eligible(p));checks++;
  g=position(4,false);p=g.getPlayers().get(1);for(int i=0;i<7;i++)addCardToZone("Memnite",p,ZoneType.Hand);
  Assert.assertTrue(GgsLinePlanner.review(p,60000).status().contains("action-cap"));checks++;
  g=position(4,false);p=g.getPlayers().get(1);addCardToZone("Elvish Visionary",p,ZoneType.Hand);addCard("Forest",p);addCard("Forest",p);
  var unknown=GgsLinePlanner.review(p,60000);System.out.println("UNKNOWN "+unknown.status());Assert.assertTrue(unknown.status().contains("unknown-draw"));checks++;
 }
 void competingOrder() {
  Game g=position(4,false);Player p=g.getPlayers().get(1);Card fresh=addCard("Memnite",p);fresh.setSickness(true);fresh.setTurnInZone(5);
  var r=GgsLinePlanner.review(p,60000);System.out.println("ORDER "+r);Assert.assertEquals(r.status(),"complete-bounded");
  Assert.assertEquals(r.chosen().size(),2);Assert.assertTrue(r.chosen().get(0).label().startsWith("Kari Zev"));
  var early=r.lines().stream().filter(l->l.actions().size()==2&&l.actions().get(0).label().startsWith("Goro-Goro")).findFirst().orElseThrow();
  var late=r.lines().stream().filter(l->l.actions().equals(r.chosen())).findFirst().orElseThrow();Assert.assertTrue(late.score()>early.score());checks++;
  var incumbent=((PlayerControllerAi)p.getController()).getAi().chooseSpellAbilityToPlay();
  System.out.println("INCUMBENT "+incumbent);
  System.setProperty("dragonmind.linePlanner","true");System.setProperty("dragonmind.linePlannerMillis","60000");
  // Call the real controller wrapper; its normal stock land/removal fallbacks remain intact.
  var actual=((PlayerControllerAi)p.getController()).getAi().chooseSpellAbilityToPlay();
  Assert.assertNotNull(actual);Assert.assertEquals(actual.get(0).getHostCard().getName(),"Kari Zev, Skyship Raider");
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,actual.get(0),null));g.getStack().resolveStack();
  Assert.assertEquals(p.getLandsInPlay().stream().filter(Card::isTapped).count(),2L);Assert.assertTrue(p.getCardsIn(ZoneType.Hand).isEmpty());
  drain(g);
  var next=((PlayerControllerAi)p.getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(next);Assert.assertEquals(next.get(0).getApi(),forge.game.ability.ApiType.PumpAll);
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,next.get(0),null));drain(g);
  Assert.assertEquals(p.getLandsInPlay().stream().filter(Card::isTapped).count(),4L,"actual complete line pays four mana");
  Game running=g;
  // Match the forecast's declared combat scenario, rather than asserting that
  // two independent stock attack-target rolls must make the same assignments.
  try(PlannerContext combat=PlannerContext.enter(715518)) {g.getPhaseHandler().devAdvanceToPhase(PhaseType.MAIN2,()->drain(running));drain(g);}
  Assert.assertEquals(p.getCreaturesInPlay().size(),late.creatures(),"forecast matches actual line combat");
  Assert.assertEquals(p.getLife(),late.life());Assert.assertEquals(g.getPlayers().stream().filter(x->x!=p).mapToInt(Player::getLife).sum(),late.opponentLife());checks++;
  System.clearProperty("dragonmind.linePlanner");System.clearProperty("dragonmind.linePlannerMillis");checks++;
 }
 static void drain(Game g) {
  for(int n=0;n<64;n++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new AssertionError("unresolved stack");
 }
 void stockFallbacks() {
  Game g=position(4,false);Player p=g.getPlayers().get(1);
  System.setProperty("dragonmind.linePlanner","true");
  Card counter=addCardToZone("Counterspell",p,ZoneType.Hand);var unsupported=List.of(counter.getFirstSpellAbility());Assert.assertSame(GgsLinePlanner.select(p,unsupported),unsupported);checks++;
  Card land=addCardToZone("Island",p,ZoneType.Hand);var landAbility=land.getAllPossibleAbilities(p,true).stream().filter(forge.game.spellability.SpellAbility::isLandAbility).findFirst().orElseThrow();var stock=List.of(landAbility);Assert.assertSame(GgsLinePlanner.select(p,stock),stock);checks++;
  System.clearProperty("dragonmind.linePlanner");Assert.assertSame(GgsLinePlanner.select(p,unsupported),unsupported);checks++;
 }
 void hiddenInformation() {
  List<Double> scores=null;List<String> chosen=null;
  for(String hidden:List.of("Lightning Bolt","Counterspell","Doom Blade")) {
   Game g=position(4,false);Player p=g.getPlayers().get(1);addCardToZone(hidden,g.getPlayers().get(0),ZoneType.Hand);
   var r=GgsLinePlanner.review(p,60000);Assert.assertEquals(r.status(),"complete-bounded");
   var v=r.lines().stream().map(GgsLinePlanner.Line::score).toList();var c=r.chosen().stream().map(GgsLinePlanner.Action::label).toList();
   if(scores!=null){Assert.assertEquals(v,scores,"hidden identities cannot affect scores");Assert.assertEquals(c,chosen);}scores=v;chosen=c;
  }
  checks++;
 }
 public static void main(String[] args){LinePlannerRegression t=new LinePlannerRegression();t.initializeModel();t.reviewCase(4,false);t.reviewCase(2,false);t.reviewCase(4,true);t.boundaries();t.competingOrder();t.hiddenInformation();t.stockFallbacks();System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
