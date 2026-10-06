import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import forge.game.keyword.Keyword;
import org.testng.Assert;

public class FrostcliffRegression extends AITest {
 int checks;void pass(String s){checks++;System.out.println("PASS "+s);}
 AiController pilot(Player p){return ((PlayerControllerAi)p.getController()).getAi();}
 void stock() throws Exception {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1);System.clearProperty("forge.ai.ggsPilotPlayer");
  g.getPhaseHandler().devModeSet(forge.game.phase.PhaseType.MAIN2,ai,false);
  SpellAbility s=addCardToZone("Frostcliff Siege",ai,ZoneType.Hand).getFirstSpellAbility();s.setActivatingPlayer(ai);
  addCard("Island",ai);addCard("Mountain",ai);addCard("Swamp",ai);
  var evaluation=AiController.class.getDeclaredMethod("canPlayAndPayFor",SpellAbility.class);evaluation.setAccessible(true);
  Assert.assertEquals(evaluation.invoke(pilot(ai),s),AiPlayDecision.BadEtbEffects);pass("unselected pod pilots retain stock Frostcliff behavior");
 }
 void casting() throws Exception {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  Card frost=addCardToZone("Frostcliff Siege",ai,ZoneType.Hand);SpellAbility s=frost.getFirstSpellAbility();s.setActivatingPlayer(ai);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  Assert.assertFalse(ComputerUtilCost.canPayCost(s,ai,false));pass("Frostcliff cannot bypass payment");
  // Use a fresh position: the first query cached a position with no mana sources.
  g=initAndCreateGame();ai=g.getPlayers().get(1);opp=g.getPlayers().get(0);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  frost=addCardToZone("Frostcliff Siege",ai,ZoneType.Hand);s=frost.getFirstSpellAbility();s.setActivatingPlayer(ai);
  g.getPhaseHandler().devModeSet(forge.game.phase.PhaseType.MAIN2,ai,false);
  addCard("Island",ai);addCard("Mountain",ai);addCard("Mountain",ai);
  var evaluation=AiController.class.getDeclaredMethod("canPlayAndPayFor",SpellAbility.class);evaluation.setAccessible(true);
  Assert.assertEquals(evaluation.invoke(pilot(ai),s),AiPlayDecision.WillPlay);pass("Frostcliff passes actual cost and ETB decision path");
  fillLibrary(ai,10);fillLibrary(opp,10);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,s,null));g.getStack().resolveStack();
  final int frostId=frost.getId();
  Card resolved=ai.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getId()==frostId).findFirst().orElseThrow();
  Assert.assertEquals(resolved.getChosenMode(),"Jeskai");pass("actual cast resolves existing Jeskai choice");
 }
 void temur(){
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  addCard("Tetsuko Umezawa, Fugitive",ai);Card kari=addCard("Kari Zev, Skyship Raider",ai),ragavan=addToken("ragavan",ai),bear=addCard("Runeclaw Bear",opp);
  g.getAction().checkStateEffects(true);Assert.assertFalse(forge.game.combat.CombatUtil.canBlock(kari,bear));
  Card frost=addCard("Frostcliff Siege",ai);frost.setChosenMode("Temur");g.getAction().checkStateEffects(true);
  Assert.assertEquals(kari.getNetPower(),2);Assert.assertTrue(kari.hasKeyword(Keyword.HASTE));Assert.assertTrue(kari.hasKeyword(Keyword.TRAMPLE));
  Assert.assertTrue(forge.game.combat.CombatUtil.canBlock(kari,bear));pass("Temur boosts Kari out of Tetsuko's access condition");
  Assert.assertEquals(ragavan.getNetToughness(),1);Assert.assertFalse(forge.game.combat.CombatUtil.canBlock(ragavan,bear));pass("Temur preserves toughness-one Ragavan access");
 }
 public static void main(String[]args)throws Exception{FrostcliffRegression t=new FrostcliffRegression();t.initializeModel();Assert.assertEquals(forge.MulliganDefs.getDefaultRule(),forge.MulliganDefs.MulliganRule.London);t.pass("default remains London mulligans");t.stock();t.casting();t.temur();System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
