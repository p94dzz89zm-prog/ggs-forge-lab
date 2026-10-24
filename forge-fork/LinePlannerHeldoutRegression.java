import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Fresh constructed evaluation only. Never outcome-learning or natural games. */
public class LinePlannerHeldoutRegression extends AITest {
 int checks;
 void scenario(String incoming,int mode) {
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player p=g.getPlayers().get(1);
  System.setProperty("forge.ai.ggsPilotPlayer",p.getName());for(Player s:g.getPlayers())fillLibrary(s,12);
  Card commander=addCard("Goro-Goro and Satoru",p);commander.setCommander(true);commander.setSickness(false);commander.setTurnInZone(-1);
  addCardToZone(incoming,p,ZoneType.Hand);for(int i=0;i<4;i++)addCard(i==0?"Island":"Mountain",p);
  for(Player s:g.getPlayers())if(s!=p){
   if(mode==1)for(int j=0;j<3;j++){Card b=addCard("Colossal Dreadmaw",s);b.setSickness(false);b.setTurnInZone(-1);}
   if(mode==2)addCard("Propaganda",s);
  }
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(mode==3?PhaseType.MAIN2:PhaseType.MAIN1,p,false,7);
  String before=PlannerSnapshot.forPlayer(p).toString();var r=GgsLinePlanner.review(p,60000);System.out.println("HELDOUT "+incoming+" mode="+mode+" "+r);
  Assert.assertEquals(r.status(),"complete-bounded");Assert.assertEquals(PlannerSnapshot.forPlayer(p).toString(),before);
  var predicted=r.lines().stream().filter(l->l.actions().equals(r.chosen())).findFirst().orElseThrow();
  for(var a:r.chosen()) {
   var sa=GgsLinePlanner.find(p,a);Assert.assertNotNull(sa);sa.setActivatingPlayer(p);Assert.assertTrue(sa.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(sa,p,false));
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,sa,null));LinePlannerRegression.drain(g);
  }
  if(mode!=3)try(PlannerContext common=PlannerContext.enter(715518)){g.getPhaseHandler().devAdvanceToPhase(PhaseType.MAIN2,()->LinePlannerRegression.drain(g));LinePlannerRegression.drain(g);}
  Assert.assertEquals(p.getCreaturesInPlay().size(),predicted.creatures());Assert.assertEquals(p.getLife(),predicted.life());
  Assert.assertEquals(g.getPlayers().stream().filter(x->x!=p).mapToInt(Player::getLife).sum(),predicted.opponentLife());
  Assert.assertEquals((int)p.getLandsInPlay().stream().filter(c->!c.isTapped()).count(),predicted.untappedLands());checks++;
 }
 public static void main(String[] args){if(args.length!=2||!args[0].equals("--purpose")||!args[1].equals("heldout"))throw new IllegalArgumentException("Requires --purpose heldout");LinePlannerHeldoutRegression t=new LinePlannerHeldoutRegression();t.initializeModel();for(String c:List.of("Goblin Instigator","Fanatical Firebrand"))for(int m=0;m<4;m++)t.scenario(c,m);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
