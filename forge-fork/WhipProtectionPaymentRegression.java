import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Resource-option regression: preserving recovery must not erase payable UU. */
public class WhipProtectionPaymentRegression extends PackageRecoveryRegression {
 void test(boolean expectedProtection){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(2);for(int i=0;i<3;i++)addCard("Swamp",opp);for(Player p:g.getPlayers())fillLibrary(p,30);ai.setLife(7,null);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  for(String n:List.of("Swamp","Swamp","Swamp","Swamp","Island","Island","Island","Mountain"))addCard(n,ai);Card leader=addCard("Goro-Goro and Satoru",ai);addToken("r_5_5_dragon_spirit_flying",ai);
  Card whip=addCardToZone("Whip of Erebos",ai,ZoneType.Hand),counter=addCardToZone("Counterspell",ai,ZoneType.Hand);addCardToZone("Baleful Strix",ai,ZoneType.Graveyard);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);Assert.assertEquals(choices.get(0).getHostCard(),whip);play(ai,choices.get(0));SpellAbility response=counter.getFirstSpellAbility();response.setActivatingPlayer(ai);boolean payable=ComputerUtilCost.canPayCost(response,ai,false);Assert.assertEquals(payable,expectedProtection);
  if(expectedProtection){SpellAbility removal=addCardToZone("Murder",opp,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(opp);Assert.assertTrue(removal.canTarget(leader));removal.getTargets().add(leader);Assert.assertTrue(removal.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(removal,opp,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(opp,removal,null));Assert.assertTrue(response.canPlay());Assert.assertTrue(response.canTarget(removal));response.getTargets().add(removal);play(ai,response);Assert.assertTrue(ai.getCreaturesInPlay().stream().anyMatch(c->c.getId()==leader.getId()));Assert.assertTrue(opp.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getName().equals("Murder")));Assert.assertTrue(ai.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getName().equals("Counterspell")));}
  groups++;System.out.println("WHIP_PROTECTION counterspellManaPayable="+payable);
 }
 public static void main(String[]args){var t=new WhipProtectionPaymentRegression();t.initializeModel();t.test(Boolean.parseBoolean(args[0]));System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
