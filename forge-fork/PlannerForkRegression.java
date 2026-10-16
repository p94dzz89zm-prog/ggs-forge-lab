import forge.ai.*;
import forge.ai.ggs.*;
import forge.ai.simulation.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import forge.util.MyRandom;
import org.testng.Assert;
import java.util.*;

public class PlannerForkRegression extends AITest {
 public static void main(String[] args) {
  int checks=0;PlannerForkRegression t=new PlannerForkRegression();t.initializeModel();
  Game game=t.initAndCreateThreePlayerGame();Player ai=game.getPlayers().get(1),opp=game.getPlayers().get(0);
  game.EXPERIMENTAL_RESTORE_SNAPSHOT=false;
  for(Player p:game.getPlayers())t.fillLibrary(p,12);
  t.addCardToZone("Kari Zev, Skyship Raider",ai,ZoneType.Hand);
  t.addCardToZone("Lightning Bolt",opp,ZoneType.Hand);
  Card ggs=t.addCard("Goro-Goro and Satoru",ai);ggs.setSickness(false);ggs.setCommander(true);ggs.setTurnInZone(1);
  for(String land:List.of("Island","Mountain","Mountain","Swamp"))t.addCard(land,ai);
  game.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false,5);
  String before=PlannerSnapshot.forPlayer(ai).toString();Random original=MyRandom.getRandom();Random rng=new Random(801);MyRandom.setRandom(rng);
  try(PlannerContext scope=PlannerContext.enter(91)) {
   String oldAudit=System.getProperty("forge.audit.directory");java.nio.file.Path branchAudit=java.nio.file.Path.of(System.getProperty("user.home"),"branch-only-audit");System.setProperty("forge.audit.directory",branchAudit.toString());
   boolean[] inherited={false};Thread worker=new Thread(()->{inherited[0]=PlannerContext.active();forge.ai.bridge.BridgeAudit.evaluation(ai,ggs.getFirstSpellAbility(),"branch must stay private projection");});worker.start();try{worker.join();}catch(InterruptedException e){throw new AssertionError(e);}Assert.assertTrue(inherited[0],"branch evaluation thread inherits audit suppression");Assert.assertFalse(java.nio.file.Files.exists(branchAudit),"no projected worker evaluation in actual-game audit");if(oldAudit==null)System.clearProperty("forge.audit.directory");else System.setProperty("forge.audit.directory",oldAudit);
   GameCopier copier=new GameCopier(game);Game fork=copier.makeCopy(null,ai);Player selected=copier.find(ai),enemy=copier.find(opp);
   Assert.assertNotSame(fork,game);checks++;Assert.assertEquals(selected.getCardsIn(ZoneType.Hand).get(0).getName(),"Kari Zev, Skyship Raider");checks++;
   Assert.assertEquals(enemy.getCardsIn(ZoneType.Hand).get(0).getName(),PlannerContext.UNKNOWN);checks++;
   for(Card c:fork.getCardsIn(ZoneType.Library))Assert.assertEquals(c.getName(),PlannerContext.UNKNOWN);checks++;
   Assert.assertEquals(copier.find(ggs).getTurnInZone(),ggs.getTurnInZone());Assert.assertTrue(copier.find(ggs).isCommander());Assert.assertEquals(copier.find(ggs).getOracleText(),ggs.getOracleText());checks++;
   var cast=selected.getCardsIn(ZoneType.Hand).get(0).getFirstSpellAbility();cast.setActivatingPlayer(selected);
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(selected,cast,null));fork.getStack().resolveStack();
   Assert.assertTrue(selected.getCardsIn(ZoneType.Hand).isEmpty());Assert.assertEquals(ai.getCardsIn(ZoneType.Hand).size(),1);Assert.assertEquals(selected.getLandsInPlay().stream().filter(Card::isTapped).count(),2L);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),0L);checks++;
   MyRandom.getRandom().nextInt();
  }
  Assert.assertSame(MyRandom.getRandom(),rng);Assert.assertEquals(rng.nextInt(),new Random(801).nextInt(),"branch did not advance live RNG");MyRandom.setRandom(original);checks++;Assert.assertEquals(PlannerSnapshot.forPlayer(ai).toString(),before);Assert.assertFalse(PlannerContext.active());checks++;
  System.out.println("Checks passed: "+checks);System.exit(0);
 }
}
