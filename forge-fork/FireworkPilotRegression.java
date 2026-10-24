import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

public class FireworkPilotRegression extends AITest {
 int checks;
 void pass(String name) { System.out.println("PASS " + name); checks++; }
 void enable(Player ai) { System.setProperty("forge.ai.ggsPilotPlayer", ai.getName()); }
 AiController pilot(Player ai) { return ((PlayerControllerAi)ai.getController()).getAi(); }
 SpellAbility spell(Player ai, String name) {
  SpellAbility sa = addCardToZone(name,ai,ZoneType.Hand).getFirstSpellAbility(); sa.setActivatingPlayer(ai); return sa;
 }
 void factory(String name) {
  Game g=initAndCreateGame(); Player ai=g.getPlayers().get(1); enable(ai);
  addCard("Goro-Goro and Satoru",ai).setCommander(true);
  for(String land:List.of("Mountain","Mountain","Mountain","Island","Swamp"))addCard(land,ai);
  SpellAbility sa=spell(ai,name);
  Assert.assertTrue(pilot(ai).canPlaySa(sa).willingToPlay(),name);
  pass(name+" affordable MAIN1");
 }
 void costAndGate() throws Exception {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1); enable(ai);
  SpellAbility sa=spell(ai,"Urabrask's Forge");
  var eval=AiController.class.getDeclaredMethod("canPlayAndPayFor",SpellAbility.class);eval.setAccessible(true);
  Assert.assertEquals(eval.invoke(pilot(ai),sa),AiPlayDecision.CantAfford);pass("MAIN1 does not bypass mana cost");
  System.clearProperty("forge.ai.ggsPilotPlayer");
  Assert.assertFalse(ComputerUtil.castPermanentInMain1(ai,sa));pass("stock factory timing unchanged");
 }
 void colorChoices() throws Exception {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1);enable(ai);
  addCardToZone("Goro-Goro and Satoru",ai,ZoneType.Command).setCommander(true);
  addCard("Underground River",ai);addCard("Swamp",ai);
  Card redundant=addCardToZone("Watery Grave",ai,ZoneType.Hand), fixing=addCardToZone("Mana Confluence",ai,ZoneType.Hand);
  var choose=AiController.class.getDeclaredMethod("chooseBestLandToPlay",CardCollection.class);choose.setAccessible(true);
  Assert.assertEquals(choose.invoke(pilot(ai),new CardCollection(List.of(redundant,fixing))),fixing);pass("actual land chooser fixes missing red");
  Game h=initAndCreateGame();ai=h.getPlayers().get(1);enable(ai);
  addCardToZone("Goro-Goro and Satoru",ai,ZoneType.Command).setCommander(true);
  addCard("Island",ai);addCard("Mountain",ai);
  Card steam=addCardToZone("Steam Vents",ai,ZoneType.Library),watery=addCardToZone("Watery Grave",ai,ZoneType.Library);
  SpellAbility fetch=addCard("Polluted Delta",ai).getSpellAbilities().stream().filter(s->s.getApi()==forge.game.ability.ApiType.ChangeZone).findFirst().orElseThrow();fetch.setActivatingPlayer(ai);
  Assert.assertEquals(forge.ai.ability.ChangeZoneAi.chooseCardToHiddenOriginChangeZone(ZoneType.Battlefield,List.of(ZoneType.Library),fetch,new CardCollection(List.of(steam,watery)),ai,ai),watery);
  pass("actual fetch chooser fixes missing black");
  System.clearProperty("forge.ai.ggsPilotPlayer");Assert.assertEquals(FireworkPilotPolicy.preferMissingColorLands(ai,new CardCollection(List.of(steam,watery))).size(),2);pass("stock fixing policy untouched");
 }
 void coverChoices() {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enable(ai);
  addCard("Goro-Goro and Satoru",ai);addCard("Moon-Circuit Hacker",ai);
  for(String n:List.of("Shao Jun","Ezio Auditore da Firenze","Royal Assassin","Thalia, Guardian of Thraben"))addCard(n,opp);
  addCard("Runeclaw Bear",opp);addCard("Runeclaw Bear",ai);
  Card cover=addCardToZone("Cover of Darkness",ai,ZoneType.Hand);
  SpellAbility sa=forge.game.ability.AbilityFactory.getAbility(cover.getSVar("ChooseCT"),cover);sa.setActivatingPlayer(ai);
  Assert.assertEquals(ComputerUtil.chooseSomeType(ai,"Creature",sa,List.of("Human","Ninja","Dragon")),"Ninja");
  pass("Cover choice prefers Ninja over opposing Human benefit");
  for(Card c:opp.getCreaturesInPlay())Assert.assertFalse(c.hasKeyword(forge.game.keyword.Keyword.FEAR));
  pass("type evaluation does not mutate opponents or card rules");
 }
 void march(boolean enabled,boolean mana,boolean attack) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  if(enabled)enable(ai);else System.clearProperty("forge.ai.ggsPilotPlayer");
  if(mana){addCard("Island",ai);addCard("Mountain",ai);}
  Card enemy=addCard("Shao Jun",opp);enemy.setSickness(false);ai.setLife(1,null);
  if(attack){Combat c=new Combat(opp);c.addAttacker(enemy,ai);c.setBlocked(enemy,false);g.getPhaseHandler().setCombat(c);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);}
  SpellAbility sa=spell(ai,"March of Swirling Mist");
  boolean play=pilot(ai).canPlaySa(sa).willingToPlay();
  Assert.assertEquals(play,enabled&&mana&&attack);
  if(play){
   Assert.assertEquals(sa.getXManaCostPaid().intValue(),1);Assert.assertTrue(sa.getTargets().getTargetCards().contains(enemy));
   fillLibrary(ai,10);fillLibrary(opp,10);
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));g.getStack().resolveStack();
   Assert.assertTrue(enemy.isPhasedOut());pass("March actually pays and phases lethal attacker");
  }else pass("March guard enabled="+enabled+" mana="+mana+" combat="+attack);
 }

 void marchWipe() {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enable(ai);
  addCard("Island",ai);addCard("Mountain",ai);Card engine=addCard("Goro-Goro and Satoru",ai);
  SpellAbility wipe=spell(opp,"Blasphemous Act");g.getStack().add(wipe);
  SpellAbility march=spell(ai,"March of Swirling Mist");
  Assert.assertTrue(pilot(ai).canPlaySa(march).willingToPlay());Assert.assertTrue(march.getTargets().getTargetCards().contains(engine));
  fillLibrary(ai,10);fillLibrary(opp,10);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,march,null));g.getStack().resolveStack();
  Assert.assertTrue(engine.isPhasedOut());g.getStack().resolveStack();Assert.assertTrue(engine.isInZone(ZoneType.Battlefield));pass("March protects engine from actual wipe resolution");
 }
 void marchAccess() {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);enable(ai);
  addCard("Island",ai);addCard("Mountain",ai);addCard("Goro-Goro and Satoru",ai);
  Card fresh=addCard("Phoenix Chick",ai),blocker=addCard("Birds of Paradise",opp);
  fresh.setSickness(false);blocker.setSickness(false);fresh.setTurnInZone(g.getPhaseHandler().getTurn());
  g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);Combat c=new Combat(ai);c.addAttacker(fresh,opp);g.getPhaseHandler().setCombat(c);fresh.setTurnInZone(g.getPhaseHandler().getTurn());
  SpellAbility sa=spell(ai,"March of Swirling Mist");Assert.assertTrue(pilot(ai).canPlaySa(sa).willingToPlay());Assert.assertTrue(sa.getTargets().getTargetCards().contains(blocker));
  pass("March selects blocker for fresh GGS connection");
 }
 void krenkoNeedsHasteColors() {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1);enable(ai);addCard("Goro-Goro and Satoru",ai);
  addCard("Mountain",ai);for(int i=0;i<4;i++)addCard("Island",ai);
  Assert.assertFalse(FireworkPilotPolicy.preCombatPermanent(ai,spell(ai,"Krenko, Tin Street Kingpin")));pass("Krenko reserves the second red for activated haste");
 }
 public static void main(String[]args)throws Exception{
  FireworkPilotRegression t=new FireworkPilotRegression();t.initializeModel();
  for(String n:List.of("Urabrask's Forge","Fire Navy Trebuchet","Krenko, Tin Street Kingpin","Loyal Apprentice","Arcane Signet","Fellwar Stone"))t.factory(n);
  t.costAndGate();t.krenkoNeedsHasteColors();t.colorChoices();t.coverChoices();t.march(true,true,true);t.march(false,true,true);t.march(true,false,true);t.march(true,true,false);t.marchWipe();t.marchAccess();
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
