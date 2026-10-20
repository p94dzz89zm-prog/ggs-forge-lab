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

/** Choice-only fixture: actual hidden delivery, no copied zone transitions. */
public class LibraryChoiceReplayRegression extends AITest {
 static JsonArray ids(Collection<Card> cards,boolean sorted){List<Integer> ids=new ArrayList<>();for(Card card:cards)ids.add(card.getId());if(sorted)Collections.sort(ids);JsonArray out=new JsonArray();ids.forEach(out::add);return out;}
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());LibraryChoiceReplayRegression test=new LibraryChoiceReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Library choice"));Player p=game.getPlayers().get(0);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
  Card forest=test.addCardToZone("Forest",p,ZoneType.Library),plains=test.addCardToZone("Plains",p,ZoneType.Library),tower=test.addCardToZone("Command Tower",p,ZoneType.Library),card=test.addCardToZone("Cultivate",p,ZoneType.Hand);var ability=card.getFirstSpellAbility();ability.setActivatingPlayer(p);card=game.getAction().moveToStack(card,ability);ability=card.getFirstSpellAbility();ability.setActivatingPlayer(p);game.getStack().add(ability);List<Card> library=new ArrayList<>();p.getCardsIn(ZoneType.Library).forEach(library::add);
  JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);String hook="forge/ai/bridge/PlayerControllerBridge.chooseSingleCardForZoneChange(Lforge/game/zone/ZoneType;Ljava/util/List;Lforge/game/spellability/SpellAbility;Lforge/game/card/CardCollection;Lforge/game/player/DelayedReveal;Ljava/lang/String;ZLforge/game/player/Player;)Lforge/game/card/Card;";StringBuilder input=new StringBuilder();
  for(int i=0;i<2;i++){JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",i);row.addProperty("hook",hook);row.addProperty("actor_id",p.getId());row.addProperty("decision_type","cultivate_library_choice");row.addProperty("source_ability",card.getId()+":"+ability.getId());row.addProperty("ability_api","ChangeZone");row.add("ability_parameters",params.deepCopy());row.add("available_card_ids",ids(i==0?List.of(forest,plains):List.of(forest),true));row.addProperty("selected_card_id",i==0?(mode.equals("invalid")?999999:plains.getId()):forest.getId());row.addProperty("search_number",i+1);row.addProperty("title","Select a card from your library ("+(i+1)+" / 2)");row.addProperty("reveal_owner_id",mode.equals("recipient")?p.getId()+1:p.getId());row.add("reveal_card_ids",i==0?ids(library,false):JsonNull.INSTANCE);row.addProperty("reveal_message",i==0?"Cultivate - Looking at cards in ":null);input.append(row).append('\n');}input.append("{\"kind\":\"decision_tape_complete\",\"decisions\":2}\n");
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,input,StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());DurableEvidence.begin("library-choice-fixture");EngineEvidence.begin(game);
  try{
   DelayedReveal reveal=new DelayedReveal(p.getCardsIn(ZoneType.Library),Set.of(ZoneType.Library),p.getView(),"Cultivate - Looking at cards in ");Card first=p.getController().chooseSingleCardForZoneChange(ZoneType.Library,List.of(ZoneType.Library),ability,new CardCollection(List.of(plains,forest)),reveal,"Select a card from your library (1 / 2)",true,p);if(!mode.equals("valid"))throw new AssertionError("Invalid hidden choice accepted");Card second=p.getController().chooseSingleCardForZoneChange(ZoneType.Library,List.of(ZoneType.Library),ability,new CardCollection(List.of(forest)),null,"Select a card from your library (2 / 2)",true,p);
   if(first!=plains||second!=forest||!ids(library,false).equals(ids(new ArrayList<>(p.getCardsIn(ZoneType.Library)),false))||game.getStack().size()!=1||!tower.isInZone(ZoneType.Library))throw new AssertionError("Choice copied a zone outcome");DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",111);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),111,"choice-only fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS actual private look and two basic-land choices; presentation order ignored, actual library order unchanged; no resolution claimed");
  }catch(IllegalStateException error){String expected=mode.equals("invalid")?"Unavailable Cultivate":"look owner/zone/message";if(mode.equals("valid")||!error.getMessage().contains(expected))throw error;if(!ids(library,false).equals(ids(new ArrayList<>(p.getCardsIn(ZoneType.Library)),false)))throw new AssertionError("Rejected choice moved library cards");System.out.println("PASS "+mode+" hidden choice rejected before disclosure or zone mutation");}
  System.exit(0);
 }
}
