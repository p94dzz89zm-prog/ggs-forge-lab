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

/** Recorded Phoenix attack with legal live defenders and invalid-choice controls. */
public class AttackReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);System.setProperty("forge.audit.directory",root.resolve("audit").toString());
  AttackReplayRegression test=new AttackReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Attack trace"));Player p=game.getPlayers().get(0);for(Player seat:game.getPlayers())test.fillLibrary(seat,10);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Phoenix Chick",p,ZoneType.Battlefield);game.getAction().checkStaticAbilities();forge.game.combat.Combat combat=new forge.game.combat.Combat(p);if(mode.equals("tapped"))card.setTapped(true);
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/ai/bridge/PlayerControllerBridge.declareAttackers(Lforge/game/player/Player;Lforge/game/combat/Combat;)V");row.addProperty("decision_type","single_phoenix_attack");row.addProperty("attacker_id",card.getId());row.addProperty("defender_player_id",mode.equals("self")?p.getId():game.getPlayers().get(1).getId());JsonObject context=new JsonObject();context.addProperty("turn",game.getPhaseHandler().getTurn());context.addProperty("phase","COMBAT_DECLARE_ATTACKERS");context.addProperty("turn_player_id",p.getId());row.add("context",context);Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());DurableEvidence.begin("attack-replay-fixture");EngineEvidence.begin(game);
  try{p.getController().declareAttackers(p,combat);if(!mode.equals("valid"))throw new AssertionError("Illegal attack accepted");if(combat.getAttackers().size()!=1||combat.getDefenderByAttacker(card)!=game.getPlayers().get(1)||card.isTapped()||!forge.game.combat.CombatUtil.validateAttackers(combat))throw new AssertionError("Actual combat choice or premature tap diverged");DecisionReplay.finish();EngineEvidence.finish();JsonObject result=new JsonObject();result.addProperty("seed",101);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),101,"fixture\nDragonMind Result: "+result+"\n",result);System.out.println("PASS actual four-player recorded Phoenix attack; real Combat declaration, caller retains tapping/effect responsibility");}
  catch(IllegalStateException error){if(mode.equals("valid")||!error.getMessage().contains("Illegal attack creature/defender"))throw error;if(!combat.getAttackers().isEmpty())throw new AssertionError("Invalid declaration mutated combat");System.out.println("PASS actual four-player invalid "+mode+" declaration rejected before combat mutation");}System.exit(0);
 }
}
