import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import forge.util.collect.FCollection;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Recorded player membership and optional decline, without effect outcome copying. */
public class SinglePlayerReplayRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);SinglePlayerReplayRegression test=new SinglePlayerReplayRegression();test.initializeModel();test.initAndCreateGame();List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Player choice"));Player p=game.getPlayers().get(0),other=game.getPlayers().get(1);game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone("Frodo, Adventurous Hobbit",p,ZoneType.Battlefield);var ability=card.getTriggers().stream().filter(t->t.getOverridingAbility()!=null&&String.valueOf(t.getOverridingAbility().getApi()).equals("ChangeZone")).findFirst().orElseThrow().getOverridingAbility().copy();ability.setActivatingPlayer(p);
  boolean optional=mode.equals("decline");JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook",p.getController().getClass().getName().replace('.','/')+".chooseSingleEntityForEffect(Lforge/util/collect/FCollectionView;Lforge/game/player/DelayedReveal;Lforge/game/spellability/SpellAbility;Ljava/lang/String;ZLforge/game/player/Player;Ljava/util/Map;)Lforge/game/GameEntity;");row.addProperty("decision_type","single_player_effect");row.addProperty("source_ability",card.getId()+":"+ability.getId());row.addProperty("ability_api","ChangeZone");JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);row.add("ability_parameters",params);row.addProperty("title","Chooser:");row.addProperty("optional",optional);JsonArray ids=new JsonArray();ids.add(p.getId());ids.add(other.getId());row.add("available_player_ids",ids);if(optional)row.add("selected_player_id",JsonNull.INSTANCE);else row.addProperty("selected_player_id",mode.equals("invalid")?99999:other.getId());Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try{Player selected=p.getController().chooseSingleEntityForEffect(new FCollection<Player>(List.of(p,other)),null,ability,"Chooser:",optional,null,null);if(mode.equals("invalid"))throw new AssertionError("Unoffered player accepted");if(selected!=(optional?null:other)||!game.getStack().isEmpty()||!card.isInZone(ZoneType.Battlefield))throw new AssertionError("Choice copied effect outcome");DecisionReplay.finish();System.out.println("PASS four-player "+mode+": recorded actual player choice; no effect/state outcome copied");}
  catch(IllegalStateException error){if(!mode.equals("invalid")||!error.getMessage().contains("Unavailable selected player"))throw error;System.out.println("PASS four-player unoffered player rejected with diagnostic");}System.exit(0);
 }
}
