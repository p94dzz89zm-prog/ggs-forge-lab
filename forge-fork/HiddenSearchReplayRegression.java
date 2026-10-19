import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Explicit accept/decline choices; prompt mismatch rejects without effect execution. */
public class HiddenSearchReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());HiddenSearchReplayRegression test=new HiddenSearchReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Confirmation"));Player p=game.getPlayers().get(0);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Frodo, Adventurous Hobbit",p,ZoneType.Battlefield);var ability=card.getTriggers().stream().filter(t->t.getOverridingAbility()!=null&&String.valueOf(t.getOverridingAbility().getApi()).equals("ChangeZone")).findFirst().orElseThrow().getOverridingAbility().copy();ability.setActivatingPlayer(p);
  test.addCardToZone("Forest",p,ZoneType.Library);test.addCardToZone("Swamp",p,ZoneType.Library);ability.getTargets().add(p);DelayedReveal reveal=new DelayedReveal(p.getCardsIn(ZoneType.Library),Set.of(ZoneType.Library),p.getView(),"Looking at cards in ");
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/ai/bridge/PlayerControllerBridge.chooseSingleCardForZoneChange(Lforge/game/zone/ZoneType;Ljava/util/List;Lforge/game/spellability/SpellAbility;Lforge/game/card/CardCollection;Lforge/game/player/DelayedReveal;Ljava/lang/String;ZLforge/game/player/Player;)Lforge/game/card/Card;");row.addProperty("decision_type","empty_partner_search");row.addProperty("source_ability",card.getId()+":"+ability.getId());row.addProperty("ability_api","ChangeZone");JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);row.add("ability_parameters",params);row.addProperty("reveal_owner_id",mode.equals("recipient")?1:p.getId());row.addProperty("reveal_message","Looking at cards in ");row.addProperty("title","Select a card from your library");row.add("selected_card_id",JsonNull.INSTANCE);JsonArray ids=new JsonArray();for(Card c:p.getCardsIn(ZoneType.Library))ids.add(c.getId());if(mode.equals("domain"))ids.add(99999);row.add("reveal_card_ids",ids);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  System.setProperty("forge.audit.directory",root.resolve("audit").toString());DurableEvidence.begin("hidden-search-fixture");EngineEvidence.begin(game);
  try{Card selected=p.getController().chooseSingleCardForZoneChange(ZoneType.Hand,List.of(ZoneType.Library),ability,new CardCollection(),reveal,"Select a card from your library",true,p);if(!mode.equals("valid"))throw new AssertionError("Invalid reveal accepted");if(selected!=null||p.getCardsIn(ZoneType.Library).size()!=2)throw new AssertionError("Search copied an outcome");DecisionReplay.finish();System.out.println("PASS four-player empty search delivered only to searcher; actual library unchanged by choice");}
  catch(IllegalStateException error){String expected=mode.equals("domain")?"library order/domain":"owner/zone/message";if(mode.equals("valid")||!error.getMessage().contains(expected))throw error;System.out.println("PASS four-player invalid "+mode+" rejected before reveal");}EngineEvidence.finish();if(mode.equals("valid")){JsonObject result=new JsonObject();result.addProperty("seed",100);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),100,"fixture\nDragonMind Result: "+result+"\n",result);System.out.println("SEALED targeted fixture; not a complete Commander game");}System.exit(0);
 }
}
