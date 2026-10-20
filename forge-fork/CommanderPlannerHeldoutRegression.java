import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Fresh post-freeze seven-mana, short-mana and missing-color command cases. */
public class CommanderPlannerHeldoutRegression extends AITest {
 int checks;
 void scenario(int lands,boolean black) {
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player p=g.getPlayers().get(1);
  System.setProperty("forge.ai.ggsPilotPlayer",p.getName());System.setProperty("dragonmind.linePlanner","true");
  for(Player s:g.getPlayers())fillLibrary(s,12);
  Card c=addCardToZone("Goro-Goro and Satoru",p,ZoneType.Command);c.setCommander(true);p.addCommander(c);p.createCommanderEffect();p.incCommanderCast(c);p.incCommanderCast(c);
  addCardToZone("Draconic Visitor",p,ZoneType.Hand);addCardToZone("Kari Zev, Skyship Raider",p,ZoneType.Hand);
  for(int n=0;n<lands;n++)addCard(n==0?"Island":n==1&&black?"Swamp":"Mountain",p);
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,9);
  var abilities=ComputerUtilAbility.getOriginalAndAltCostAbilities(ComputerUtilAbility.getSpellAbilities(new CardCollection(c),p),p);
  var sa=abilities.stream().filter(x->{x.setActivatingPlayer(p);return x.isSpell()&&x.canPlay();}).findFirst().orElseThrow();
  boolean payable=lands>=7&&black;Assert.assertEquals(ComputerUtilCost.canPayCost(sa,p,false),payable);var stock=List.of(sa);String before=PlannerSnapshot.forPlayer(p).toString();
  Assert.assertSame(GgsLinePlanner.select(p,stock),stock);Assert.assertEquals(PlannerSnapshot.forPlayer(p).toString(),before);
  Assert.assertEquals(ComputerUtil.handlePlayingSpellAbility(p,sa,null),payable);
  if(payable){LinePlannerRegression.drain(g);Assert.assertTrue(p.getCreaturesInPlay().stream().anyMatch(x->x.getId()==c.getId()));Assert.assertEquals((int)p.getLandsInPlay().stream().filter(Card::isTapped).count(),7);}
  else{Assert.assertEquals(PlannerSnapshot.forPlayer(p).toString(),before);Assert.assertTrue(p.getCardsIn(ZoneType.Command).stream().anyMatch(x->x.getId()==c.getId()));Assert.assertTrue(g.getStack().isEmpty());}
  System.clearProperty("dragonmind.linePlanner");System.out.println("HELDOUT COMMAND lands="+lands+" black="+black+" paid="+payable);checks++;
 }
 public static void main(String[]args){if(!Arrays.equals(args,new String[]{"--purpose","heldout"}))throw new IllegalArgumentException("Requires --purpose heldout");CommanderPlannerHeldoutRegression t=new CommanderPlannerHeldoutRegression();t.initializeModel();t.scenario(7,true);t.scenario(6,true);t.scenario(7,false);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
