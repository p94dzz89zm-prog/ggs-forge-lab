import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Reproduces an unsupported commander cast being displaced by hand development. */
public class CommanderPlannerScopeRegression extends AITest {
 int checks;
 void scenario(int priorCasts,int lands) {
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player p=g.getPlayers().get(1);
  System.setProperty("forge.ai.ggsPilotPlayer",p.getName());System.setProperty("dragonmind.linePlanner","true");System.setProperty("dragonmind.linePlannerMillis","60000");
  for(Player s:g.getPlayers())fillLibrary(s,12);
  Card c=addCardToZone("Goro-Goro and Satoru",p,ZoneType.Command);c.setCommander(true);p.addCommander(c);p.createCommanderEffect();
  for(int n=0;n<priorCasts;n++)p.incCommanderCast(c);
  addCardToZone("Kari Zev, Skyship Raider",p,ZoneType.Hand);
  for(int n=0;n<lands;n++)addCard(n==0?"Island":n==1?"Swamp":"Mountain",p);
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,6);
  var abilities=ComputerUtilAbility.getOriginalAndAltCostAbilities(ComputerUtilAbility.getSpellAbilities(new CardCollection(c),p),p);
  for(var candidate:abilities){candidate.setActivatingPlayer(p);System.out.println("COMMAND ABILITY canPlay="+candidate.canPlay()+" costs="+candidate.getPayCosts()+" "+candidate);}
  var sa=abilities.stream().filter(x->x.isSpell()&&x.canPlay()).findFirst().orElseGet(()->abilities.stream().filter(x->x.isSpell()).findFirst().orElseThrow());sa.setActivatingPlayer(p);var stock=List.of(sa);
  boolean payable=ComputerUtilCost.canPayCost(sa,p,false);Assert.assertEquals(payable,lands>=3+priorCasts*2);
  var chosen=GgsLinePlanner.select(p,stock);System.out.println("COMMAND prior="+priorCasts+" lands="+lands+" stock="+stock+" chosen="+chosen);
  Assert.assertSame(chosen,stock,"a cast outside the action search must never be overridden");
  if(payable){Assert.assertTrue(sa.canPlay(),"ordinary command cast timing");Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,sa,null),"command actual payment");LinePlannerRegression.drain(g);Assert.assertTrue(p.getCreaturesInPlay().stream().anyMatch(x->x.getId()==c.getId()),"commander resolved onto battlefield");Assert.assertEquals((int)p.getLandsInPlay().stream().filter(Card::isTapped).count(),3+priorCasts*2);}
  else {Assert.assertFalse(ComputerUtil.handlePlayingSpellAbility(p,sa,null));Assert.assertTrue(c.isInZone(ZoneType.Command));Assert.assertEquals((int)p.getLandsInPlay().stream().filter(Card::isTapped).count(),0);}
  System.clearProperty("dragonmind.linePlanner");System.clearProperty("dragonmind.linePlannerMillis");checks++;
 }
 public static void main(String[]args){CommanderPlannerScopeRegression t=new CommanderPlannerScopeRegression();t.initializeModel();t.scenario(0,3);t.scenario(1,5);t.scenario(1,3);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
