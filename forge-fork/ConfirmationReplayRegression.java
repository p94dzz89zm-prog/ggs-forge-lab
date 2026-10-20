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
public class ConfirmationReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];boolean accept=mode.equals("accept");Path root=Path.of(args[1]);Files.createDirectories(root);ConfirmationReplayRegression test=new ConfirmationReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Confirmation"));Player p=game.getPlayers().get(0);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Frodo, Adventurous Hobbit",p,ZoneType.Battlefield);var ability=card.getTriggers().stream().filter(t->t.getOverridingAbility()!=null&&String.valueOf(t.getOverridingAbility().getApi()).equals("ChangeZone")).findFirst().orElseThrow().getOverridingAbility().copy();ability.setActivatingPlayer(p);
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook","forge/game/player/PlayerController.confirmAction(Lforge/game/spellability/SpellAbility;Lforge/game/player/PlayerActionConfirmMode;Ljava/lang/String;Ljava/util/Map;)Z");row.addProperty("decision_type","confirm_action");row.addProperty("source_ability",card.getId()+":"+ability.getId());row.addProperty("ability_api","ChangeZone");JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);row.add("ability_parameters",params);row.addProperty("mode","ChangeZoneGeneral");row.addProperty("title",mode.equals("mismatch")?"Different prompt":"Search your library?");row.addProperty("accept",accept);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try{boolean selected=p.getController().confirmAction(ability,PlayerActionConfirmMode.ChangeZoneGeneral,"Search your library?",null);if(mode.equals("mismatch"))throw new AssertionError("Mismatched prompt accepted");if(selected!=accept||!game.getStack().isEmpty()||!card.isInZone(ZoneType.Battlefield))throw new AssertionError("Confirmation applied effect outcome");DecisionReplay.finish();System.out.println("PASS four-player "+mode+": recorded confirmation; no search/effect outcome copied");}
  catch(IllegalStateException error){if(!mode.equals("mismatch")||!error.getMessage().contains("prompt/mode/context"))throw error;System.out.println("PASS four-player mismatched confirmation prompt rejected");}System.exit(0);
 }
}
