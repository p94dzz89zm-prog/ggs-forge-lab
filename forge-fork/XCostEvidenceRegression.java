import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.phase.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;

/** Actual X spell payment/resolution, with an intentionally stale cast history. */
public class XCostEvidenceRegression extends AITest {
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[0]);System.setProperty("forge.audit.directory",root.resolve("audit/x").toString());
  XCostEvidenceRegression test=new XCostEvidenceRegression();test.initializeModel();
  Game game=test.initAndCreateThreePlayerGame();Player player=game.getPlayers().get(1);
  for(Player p:game.getPlayers())test.fillLibrary(p,10);
  for(int i=0;i<4;i++)test.addCard("Forest",player);
  Card hydra=test.addCardToZone("Voracious Hydra",player,ZoneType.Hand);
  SpellAbility spell=hydra.getFirstSpellAbility();spell.setActivatingPlayer(player);spell.setXManaCostPaid(2);
  if(hydra.getCastSA()!=null)throw new AssertionError("Control needs unavailable cast history");
  var encode=EngineEvidence.class.getDeclaredMethod("value",Object.class,int.class);encode.setAccessible(true);
  DurableEvidence.begin("x-evidence");EngineEvidence.begin(game);
  JsonObject before=((JsonElement)encode.invoke(null,spell,0)).getAsJsonObject();
  if(before.get("chosen_x").getAsInt()!=2||!before.getAsJsonObject("source").get("cast_chosen_x").isJsonNull())throw new AssertionError("Chosen X confused with missing cast history");
  if(before.get("description").getAsString().contains("X=0"))throw new AssertionError("Stale description X survived");
  game.getPhaseHandler().devModeSet(PhaseType.MAIN1,player,false);
  if(!ComputerUtil.handlePlayingSpellAbility(player,spell,null))throw new AssertionError("Hydra cast failed");
  SpellAbility stacked=game.getStack().peekAbility();if(stacked.getXManaCostPaid()!=2)throw new AssertionError("X changed on stack");
  if(player.getLandsInPlay().stream().filter(Card::isTapped).count()!=4)throw new AssertionError("Expected actual2GG payment");
  game.getStack().resolveStack();Card permanent=player.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getName().equals("Voracious Hydra")).findFirst().orElseThrow();
  if(permanent.getCounters(CounterEnumType.P1P1)!=2)throw new AssertionError("Hydra must enter with two counters before its ETB resolves");
  EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",95);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("engine-records/x"),95,"fixture\nDragonMind Result: "+result+"\n",result);
  String tape=Files.readString(root.resolve("audit/x/referee-events.jsonl"));
  if(!tape.contains("\"announced_ability_available\":true")||!tape.contains("\"chosen_x\":2"))throw new AssertionError("Missing live announcement X provenance");
  System.out.println("PASS actual Hydra X2:2GG paid, stack X2, two entry counters, announced X retained; missing cast history is null");System.exit(0);
 }
}
