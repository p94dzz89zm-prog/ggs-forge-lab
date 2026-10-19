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

/** Actual Partner choice/stack, underlying identity, target evidence and invalid choice. */
public class PartnerTriggerReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];boolean invalid=mode.equals("invalid"),trace=mode.equals("trace");Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());
  PartnerTriggerReplayRegression test=new PartnerTriggerReplayRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
  GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Partner target"));Player p=game.getPlayers().get(0);for(Player seat:game.getPlayers())test.fillLibrary(seat,10);
  game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);
  Card card=test.addCardToZone("Frodo, Adventurous Hobbit",p,ZoneType.Battlefield);p.addCommander(card);game.getAction().checkStaticAbilities();
  Trigger trigger=card.getTriggers().stream().filter(t->t.getOverridingAbility()!=null&&String.valueOf(t.getOverridingAbility().getApi()).equals("ChangeZone")).findFirst().orElseThrow();
  var inner=trigger.getOverridingAbility().copy();inner.setActivatingPlayer(p);WrappedAbility wrapper=new WrappedAbility(trigger,inner,p);wrapper.setActivatingPlayer(p);
  if(!trace){
   JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/ai/PlayerControllerAi.orderAndPlaySimultaneousSa(Ljava/util/List;)V");row.addProperty("decision_type","partner_trigger_stack");row.addProperty("source_card_id",card.getId());row.addProperty("source_name",card.getName());row.addProperty("original_ability_id",wrapper.getId()+500);JsonArray targets=new JsonArray();targets.add(invalid?99999:p.getId());row.add("target_player_ids",targets);
   JsonObject payment=new JsonObject();payment.addProperty("kind","decision");payment.addProperty("index",1);payment.addProperty("actor_id",p.getId());payment.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");payment.addProperty("decision_type","zero_effect_mana");payment.addProperty("payment_choice","pay");payment.addProperty("source_ability",card.getId()+":"+(inner.getId()+1000));payment.addProperty("ability_api","ChangeZone");JsonObject params=new JsonObject();inner.getMapParams().forEach(params::addProperty);payment.add("ability_parameters",params);
   Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n"+payment+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":2}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  }
  if(trace)forge.util.MyRandom.setRandom(new EvidenceRandom(98));DurableEvidence.begin("partner-fixture");EngineEvidence.begin(game);if(trace)System.setProperty("forge.evidence.traceRandom","true");
  try{
   p.getController().orderAndPlaySimultaneousSa(List.of(wrapper));if(invalid)throw new AssertionError("Invalid player accepted");
   if(game.getStack().size()!=1||inner.getTargets().getFirstTargetedPlayer()!=p||!card.isInZone(ZoneType.Battlefield))throw new AssertionError("Actual stack or target differs");
   if(!trace){if(!p.getController().payManaCost(inner.getPayCosts().getCostPartByType(forge.game.cost.CostPartMana.class),inner,null,null,true))throw new AssertionError("Underlying zero payment failed");DecisionReplay.finish();}
   System.setProperty("forge.evidence.traceRandom","false");EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",99);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),99,"fixture\nDragonMind Result: "+result+"\n",result);
   boolean found=false;for(String line:Files.readAllLines(root.resolve("audit/referee-events.jsonl"))){JsonObject event=JsonParser.parseString(line).getAsJsonObject();if(!event.has("hook")||!event.get("hook").getAsString().startsWith("forge/game/zone/MagicStack.add(")||!event.get("kind").getAsString().equals("engine_call"))continue;JsonObject ability=event.getAsJsonArray("arguments").get(0).getAsJsonObject();JsonArray recorded=ability.getAsJsonObject("wrapped_ability").getAsJsonArray("direct_targets");found|=recorded.size()==1&&recorded.get(0).getAsJsonObject().get("player_id").getAsInt()==p.getId();}
   if(!found)throw new AssertionError("Actual underlying player target missing from evidence");System.out.println("PASS four-player "+mode+": actual Partner target/zero payment/stack; direct underlying target evidence sealed");
  }catch(IllegalStateException error){if(!invalid||!error.getMessage().contains("target player"))throw error;if(!game.getStack().isEmpty()||!inner.getTargets().isEmpty())throw new AssertionError("Invalid choice mutated stack/target");System.out.println("PASS four-player invalid Partner target rejected before mutation");}
  System.exit(0);
 }
}
