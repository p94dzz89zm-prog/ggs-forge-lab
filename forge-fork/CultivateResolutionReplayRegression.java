import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.ability.AbilityUtils;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Actual native resolution, not a copied recorded final state. */
public class CultivateResolutionReplayRegression extends AITest {
 static JsonArray ids(Iterable<Card> cards,boolean sort){List<Integer> values=new ArrayList<>();for(Card c:cards)values.add(c.getId());if(sort)Collections.sort(values);JsonArray out=new JsonArray();values.forEach(out::add);return out;}
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path directory=Path.of(args[1]);Files.createDirectories(directory);System.setProperty("forge.audit.directory",directory.resolve("audit").toString());var test=new CultivateResolutionReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));var rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Cultivate resolution"));Player p=game.getPlayers().get(0);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
  Card forest=test.addCardToZone("Forest",p,ZoneType.Library),plains=test.addCardToZone("Plains",p,ZoneType.Library),tower=test.addCardToZone("Command Tower",p,ZoneType.Library),spell=test.addCardToZone("Cultivate",p,ZoneType.Hand);var root=spell.getFirstSpellAbility();root.setActivatingPlayer(p);spell=game.getAction().moveToStack(spell,root);root=spell.getFirstSpellAbility();root.setActivatingPlayer(p);game.getStack().add(root);
  String hook="forge/ai/bridge/PlayerControllerBridge.chooseSingleCardForZoneChange(Lforge/game/zone/ZoneType;Ljava/util/List;Lforge/game/spellability/SpellAbility;Lforge/game/card/CardCollection;Lforge/game/player/DelayedReveal;Ljava/lang/String;ZLforge/game/player/Player;)Lforge/game/card/Card;";StringBuilder tape=new StringBuilder();
  for(int i=0;i<4;i++){var ability=i<2?root:i==2?root.getSubAbility():root.getSubAbility().getSubAbility();JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",i);row.addProperty("hook",hook);row.addProperty("actor_id",p.getId());row.addProperty("decision_type",i<2?"cultivate_library_choice":"cultivate_remembered_choice");row.addProperty("source_ability",spell.getId()+":"+(ability.getId()+(i<2?0:500)));row.addProperty("ability_api","ChangeZone");JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);row.add("ability_parameters",params);row.add("available_card_ids",ids(i==0||i==2?List.of(forest,plains):i==1?List.of(forest):List.of(plains),true));row.addProperty("selected_card_id",i==0||i==3?plains.getId():i==2&&mode.equals("invalid")?999999:forest.getId());row.addProperty("title",i<2?"Select a card from your library ("+(i+1)+" / 2)":ability.getParam("SelectPrompt"));if(i<2){row.addProperty("search_number",i+1);row.addProperty("reveal_owner_id",p.getId());row.add("reveal_card_ids",i==0?ids(p.getCardsIn(ZoneType.Library),false):JsonNull.INSTANCE);row.addProperty("reveal_message",i==0?"Cultivate - Looking at cards in ":null);}else row.addProperty("destination",i==2?"Battlefield":"Hand");tape.append(row).append('\n');}
  tape.append("{\"kind\":\"decision_tape_complete\",\"decisions\":4}\n");Path input=directory.resolve("decisions.jsonl");Files.writeString(input,tape,StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",input.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(input))));System.setProperty("forge.decision.replayDiagnostics",directory.resolve("diagnostics").toString());DurableEvidence.begin("cultivate-resolution");EngineEvidence.begin(game);
  try{
   AbilityUtils.resolve(root);
   if(!mode.equals("valid"))throw new AssertionError("Invalid remembered choice accepted");
   Card actual=game.getCardState(forest);if(!actual.isInZone(ZoneType.Battlefield)||!actual.isTapped()||actual.getOwner()!=p||actual.getController()!=p||!game.getCardState(plains).isInZone(ZoneType.Hand)||!tower.isInZone(ZoneType.Library)||p.getCardsIn(ZoneType.Library).size()!=1||spell.hasRemembered())throw new AssertionError("Native Cultivate resolution differs");
   DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",112);result.addProperty("status","completed");DurableEvidence.finish(directory.resolve("results"),112,"native resolution fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS actual two selections, public reveal, battlefield tapped, hand, native shuffle and cleanup; not a complete game");
  }catch(IllegalStateException error){if(!mode.equals("invalid")||!error.getMessage().contains("Unavailable Cultivate remembered"))throw error;if(!forest.isInZone(ZoneType.Library)||!plains.isInZone(ZoneType.Library))throw new AssertionError("Rejected selection moved a card");System.out.println("PASS unavailable remembered card rejected before zone mutation");}
  System.exit(0);
 }
}
