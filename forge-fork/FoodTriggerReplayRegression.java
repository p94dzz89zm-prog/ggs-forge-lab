import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import forge.game.trigger.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Actual four-player Food trigger, native token birth and illegal phase guard. */
public class FoodTriggerReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];boolean invalid=mode.equals("phase");Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());
  FoodTriggerReplayRegression test=new FoodTriggerReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
  GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Food"));Player p=game.getPlayers().get(0);for(Player seat:game.getPlayers())test.fillLibrary(seat,10);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(invalid?PhaseType.MAIN1:PhaseType.COMBAT_BEGIN,p,false);game.getPhaseHandler().setPriority(p);
  Card card=test.addCardToZone("Sam, Loyal Attendant",p,ZoneType.Battlefield);p.addCommander(card);game.getAction().checkStaticAbilities();Trigger trigger=card.getTriggers().stream().filter(t->"Phase".equals(String.valueOf(t.getMode()))).findFirst().orElseThrow();var inner=trigger.ensureAbility().copy();inner.setActivatingPlayer(p);WrappedAbility wrapper=new WrappedAbility(trigger,inner,null);wrapper.setActivatingPlayer(p);
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/ai/PlayerControllerAi.orderAndPlaySimultaneousSa(Ljava/util/List;)V");row.addProperty("decision_type","sam_food_trigger_stack");row.addProperty("source_card_id",card.getId());row.addProperty("source_name",card.getName());row.addProperty("original_ability_id",wrapper.getId()+500);
  JsonObject context=new JsonObject();context.addProperty("turn",game.getPhaseHandler().getTurn());context.addProperty("phase",String.valueOf(game.getPhaseHandler().getPhase()));context.addProperty("priority_player_id",p.getId());context.addProperty("turn_player_id",p.getId());row.add("context",context);
  JsonObject payment=new JsonObject();payment.addProperty("kind","decision");payment.addProperty("index",1);payment.addProperty("actor_id",p.getId());payment.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");payment.addProperty("decision_type","zero_effect_mana");payment.addProperty("payment_choice","pay");payment.addProperty("source_ability",card.getId()+":"+(inner.getId()+1000));payment.addProperty("ability_api","Token");JsonObject params=new JsonObject();inner.getMapParams().forEach(params::addProperty);payment.add("ability_parameters",params);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n"+payment+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":2}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());DurableEvidence.begin("food-fixture");EngineEvidence.begin(game);
  try{
   p.getController().orderAndPlaySimultaneousSa(List.of(wrapper));if(invalid)throw new AssertionError("Illegal phase accepted");
   if(game.getStack().size()!=1||!inner.getTargets().isEmpty()||p.getCardsIn(ZoneType.Battlefield).stream().anyMatch(Card::isToken))throw new AssertionError("Choice copied an outcome");
   game.getStack().resolveStack();var foods=p.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.isToken()&&c.getName().equals("Food Token")).toList();
   if(!game.getStack().isEmpty()||foods.size()!=1||foods.get(0).getOwner()!=p||foods.get(0).getController()!=p||!foods.get(0).isArtifact()||!foods.get(0).getType().hasSubtype("Food"))throw new AssertionError("Actual Food ownership/type/stack differs");
   for(Player seat:game.getPlayers())if(seat!=p&&seat.getCardsIn(ZoneType.Battlefield).stream().anyMatch(Card::isToken))throw new AssertionError("Wrong Food recipient");
   DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",107);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),107,"fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS native Food created only on resolve; source controller owns and controls it; recorded choices not outcomes");
  }catch(IllegalStateException error){if(!invalid||!error.getMessage().contains("Food trigger context"))throw error;if(!game.getStack().isEmpty()||p.getCardsIn(ZoneType.Battlefield).stream().anyMatch(Card::isToken))throw new AssertionError("Rejected phase mutated stack/token");System.out.println("PASS wrong Food trigger phase rejected before mutation");}
  System.exit(0);
 }
}
