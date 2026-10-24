import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.cost.*;
import forge.game.mana.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import forge.card.MagicColor;
import forge.card.mana.ManaCost;
import com.google.gson.*;
import org.testng.Assert;
import java.nio.file.*;
import java.util.*;

/** Actual instrumented delivery and payment paths, not hand-delta inference. */
public class EngineProvenanceRegression extends AITest {
 public static void main(String[]args)throws Exception {
  Path root=Path.of(args[0]);System.setProperty("forge.audit.directory",root.resolve("audit/fixture").toString());
  EngineProvenanceRegression t=new EngineProvenanceRegression();t.initializeModel();Game g=t.initAndCreateThreePlayerGame();Player me=g.getPlayers().get(1),other=g.getPlayers().get(0);
  for(Player p:g.getPlayers())t.fillLibrary(p,12);
  Card secret=t.addCardToZone("Demonic Tutor",me,ZoneType.Hand);Card island=t.addCard("Island",me);
  EvidenceRandom rng=new EvidenceRandom(9147);rng.nextInt(17);
  DurableEvidence.begin("provenance-fixture");EngineEvidence.begin(g);rng.nextLong();
  g.fireEvent(new forge.game.event.GameEventGameStarted(g.getRules().getGameType(),me,g.getPlayers()));
  g.getAction().reveal(new CardCollection(secret),me,true,"Public test: ");
  g.getAction().revealTo(new CardCollection(secret),other,"Private test: ");
  Assert.assertFalse(BridgeSnapshot.forPlayer(other).toString().contains("Demonic Tutor"),"Referee-only reveal must not modify pilot snapshot disclosure");
  SpellAbility produce=island.getManaAbilities().get(0);produce.setActivatingPlayer(me);
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(me,produce,null));Assert.assertTrue(island.isTapped());Assert.assertEquals(me.getManaPool().totalMana(),1);
  Card spell=t.addCardToZone("Opt",me,ZoneType.Hand);SpellAbility sa=spell.getFirstSpellAbility();sa.setActivatingPlayer(me);
  ManaCostBeingPaid cost=new ManaCostBeingPaid(ManaCost.get(1));
  Mana m=me.getManaPool().iterator().next();Assert.assertTrue(me.getManaPool().tryPayCostWithMana(sa,cost,m,false));Assert.assertEquals(cost.getConvertedManaCost(),0);Assert.assertEquals(me.getManaPool().totalMana(),0);
  ManaCostBeingPaid failed=new ManaCostBeingPaid(ManaCost.get(1));Assert.assertFalse(me.getManaPool().tryPayCostWithMana(sa,failed,m,false));
  // Test-only planning is explicitly marked, rather than counted as a paid spell.
  me.getManaPool().addMana(new Mana(MagicColor.BLUE,island,produce.getManaPart(),me));
  Assert.assertTrue(me.getManaPool().tryPayCostWithMana(sa,new ManaCostBeingPaid(ManaCost.get(1)),me.getManaPool().iterator().next(),true));
  // Exercise stack/effect/visibility encoders through actual casting and resolution.
  t.addCard("Island",me);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,me,false);
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(me,sa,null));
  g.getStack().resolveStack();Assert.assertTrue(me.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getName().equals("Opt")),"resolved physical card in graveyard");
  t.addCard("Sapphire Medallion",me);t.addCard("Island",me);t.addCard("Island",me);
  Card draw=t.addCardToZone("Divination",me,ZoneType.Hand);SpellAbility drawSa=draw.getFirstSpellAbility();drawSa.setActivatingPlayer(me);
  long tappedBefore=me.getLandsInPlay().stream().filter(Card::isTapped).count();Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(me,drawSa,null));g.getStack().resolveStack();Assert.assertEquals(me.getLandsInPlay().stream().filter(Card::isTapped).count()-tappedBefore,2L,"actual reduced Divination payment");
  Card attacker=t.addCard("Runeclaw Bear",me);attacker.setSickness(false);
  forge.game.combat.Combat combat=new forge.game.combat.Combat(me);combat.addAttacker(attacker,other);combat.setBlocked(attacker,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,me,false);
  g.fireEvent(new forge.game.event.GameEventCombatChanged());
  other.loseConditionMet(GameLossReason.Conceded,null);g.onPlayerLost(other);
  EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",91);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("engine-records/fixture"),91,"fixture\nDragonMind Result: "+result+"\n",result);
  List<JsonObject> rows=new ArrayList<>();for(String l:Files.readAllLines(root.resolve("audit/fixture/referee-events.jsonl")))rows.add(JsonParser.parseString(l).getAsJsonObject());
  JsonObject reveal=rows.stream().filter(r->r.has("visibility_operation")&&r.get("visibility_operation").getAsString().equals("reveal_all")).findFirst().orElseThrow();Assert.assertEquals(reveal.getAsJsonArray("entitled_player_ids").size(),3);
  JsonObject look=rows.stream().filter(r->r.has("visibility_operation")&&r.get("visibility_operation").getAsString().equals("look_specified")).findFirst().orElseThrow();Assert.assertEquals(look.getAsJsonArray("entitled_player_ids").size(),1);Assert.assertEquals(look.getAsJsonArray("entitled_player_ids").get(0).getAsInt(),other.getId());
  Assert.assertTrue(reveal.toString().contains("Demonic Tutor"));Assert.assertTrue(rows.stream().anyMatch(r->r.has("initial_state")));Assert.assertTrue(rows.stream().anyMatch(r->r.get("kind").getAsString().equals("engine_return")&&r.get("hook").getAsString().contains("tryPayCostWithMana")&&!r.get("result").getAsBoolean()));
  Assert.assertTrue(rows.stream().anyMatch(r->r.has("hook")&&r.get("hook").getAsString().contains("applyReduceCostAbility")&&r.toString().contains("Sapphire Medallion")),"named applied cost modifier provenance");
  JsonObject finalState=rows.get(rows.size()-1).getAsJsonObject("final_state");Assert.assertEquals(finalState.getAsJsonArray("players").size(),3);Assert.assertTrue(rows.stream().anyMatch(r->r.has("elimination_state_after")));
  Assert.assertTrue(rows.stream().anyMatch(r->r.has("combat")&&!r.get("combat").isJsonNull()));
  Assert.assertTrue(rows.stream().anyMatch(r->r.has("visibility_operation")&&r.get("visibility_operation").getAsString().equals("public_stack_announcement")));
  Assert.assertFalse(rows.toString().contains("\"unencoded\":\"forge.game.spellability.SpellAbilityStackInstance\""));
  Assert.assertEquals(rows.get(rows.size()-1).get("kind").getAsString(),"engine_tape_complete");
  java.lang.reflect.Method equivalent=EngineEvidence.class.getDeclaredMethod("equivalent",JsonObject.class,JsonObject.class);equivalent.setAccessible(true);
  JsonObject a=JsonParser.parseString("{\"arguments\":[{\"record_type\":\"GameEventCardStatsChanged\",\"cards\":[{\"view_id\":1},{\"view_id\":2}]}]}").getAsJsonObject();
  JsonObject b=JsonParser.parseString("{\"arguments\":[{\"record_type\":\"GameEventCardStatsChanged\",\"cards\":[{\"view_id\":2},{\"view_id\":1}]}]}").getAsJsonObject();
  Assert.assertTrue((Boolean)equivalent.invoke(null,a,b),"unordered notification membership");
  b.getAsJsonArray("arguments").get(0).getAsJsonObject().addProperty("record_type","GameEventZone");Assert.assertFalse((Boolean)equivalent.invoke(null,a,b),"different event cannot compare equal");
  a=JsonParser.parseString("{\"Library\":[1,2]}").getAsJsonObject();b=JsonParser.parseString("{\"Library\":[2,1]}").getAsJsonObject();Assert.assertFalse((Boolean)equivalent.invoke(null,a,b),"ordered zones remain order-sensitive");
  System.out.println("Checks passed: 19");System.out.println("PASS actual reveal recipients, private visibility, source production, spent unit, failed payment, test flag, initial state and sealed tape");System.exit(0);
 }
}
