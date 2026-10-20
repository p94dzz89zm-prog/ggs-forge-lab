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

/** Actual mandatory self costs; deliberately stops before fetch resolution. */
public class MistyActivationReplayRegression extends AITest {
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path dir=Path.of(args[1]);Files.createDirectories(dir);System.setProperty("forge.audit.directory",dir.resolve("audit").toString());var test=new MistyActivationReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));var rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Misty costs"));Player p=game.getPlayers().get(0);for(Player seat:game.getPlayers())test.fillLibrary(seat,5);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Misty Rainforest",p,ZoneType.Battlefield);var ability=card.getSpellAbilities().stream().filter(sa->"ChangeZone".equals(String.valueOf(sa.getApi()))).findFirst().orElseThrow();ability.setActivatingPlayer(p);int life=p.getLife();if(mode.equals("tapped"))card.setTapped(true);if(mode.equals("definition"))ability.getMapParams().put("ChangeType","Land");JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);
  JsonObject choose=new JsonObject();choose.addProperty("kind","decision");choose.addProperty("index",0);choose.addProperty("actor_id",p.getId());choose.addProperty("hook","forge/ai/bridge/PlayerControllerBridge.chooseSpellAbilityToPlay()Ljava/util/List;");choose.addProperty("decision_type","misty_activation");choose.addProperty("source_card_id",card.getId());choose.addProperty("original_ability_id",ability.getId()+500);choose.add("ability_parameters",params.deepCopy());JsonObject context=new JsonObject();context.addProperty("turn",game.getPhaseHandler().getTurn());context.addProperty("phase","MAIN1");context.addProperty("priority_player_id",p.getId());context.addProperty("turn_player_id",p.getId());choose.add("context",context);
  JsonObject pay=new JsonObject();pay.addProperty("kind","decision");pay.addProperty("index",1);pay.addProperty("actor_id",p.getId());pay.addProperty("hook","forge/game/player/PlayerController.payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");pay.addProperty("decision_type","misty_zero_component");pay.addProperty("source_ability",card.getId()+":"+(ability.getId()+500));pay.addProperty("ability_api","ChangeZone");pay.add("ability_parameters",params.deepCopy());Path input=dir.resolve("decisions.jsonl");Files.writeString(input,choose+"\n"+pay+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":2}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",input.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(input))));System.setProperty("forge.decision.replayDiagnostics",dir.resolve("diagnostics").toString());DurableEvidence.begin("misty-cost-fixture");EngineEvidence.begin(game);
  try{
   var selected=p.getController().chooseSpellAbilityToPlay();if(!mode.equals("valid"))throw new AssertionError("Invalid activation accepted");if(selected.size()!=1||selected.get(0)!=ability||p.getLife()!=life||!card.isInZone(ZoneType.Battlefield)||card.isTapped())throw new AssertionError("Selection copied payment outcome");
   if(!ComputerUtil.handlePlayingSpellAbility(p,ability,null))throw new AssertionError("Actual activation failed");if(p.getLife()!=life-1||!card.isTapped()||!game.getCardState(card).isInZone(ZoneType.Graveyard)||game.getStack().size()!=1||!p.getManaPool().isEmpty())throw new AssertionError("Actual mandatory costs differ");DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",113);result.addProperty("status","completed");DurableEvidence.finish(dir.resolve("results"),113,"activation-only fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS native tap, one life, self-sacrifice, zero mana and actual stack; fetch resolution not certified");
  }catch(IllegalStateException error){String expected=mode.equals("tapped")?"Unavailable Misty":"Unsupported Misty definition";if(mode.equals("valid")||!error.getMessage().contains(expected))throw error;if(p.getLife()!=life||!card.isInZone(ZoneType.Battlefield)||!game.getStack().isEmpty())throw new AssertionError("Rejected activation paid costs");System.out.println("PASS "+mode+" activation rejected without payment");}
  System.exit(0);
 }
}
