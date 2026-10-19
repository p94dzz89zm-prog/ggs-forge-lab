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

/** Four real controllers, live legal spell available, recorded pass or rejection. */
public class PriorityReplayRegression extends AITest {
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);
  PriorityReplayRegression test=new PriorityReplayRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
  GameRules rules=new GameRules(GameType.Constructed);Game game=new Game(seats,rules,new Match(rules,seats,"Priority replay regression"));game.setAge(GameStage.Play);
  Player player=game.getPlayers().get(0);for(Player p:game.getPlayers())test.fillLibrary(p,10);
  Card land=test.addCard("Mountain",player);Card bolt=test.addCardToZone("Lightning Bolt",player,ZoneType.Hand);
  var phase=game.getPhaseHandler();phase.devModeSet(PhaseType.MAIN1,player,false);phase.setPriority(player);
  var spell=bolt.getFirstSpellAbility();spell.setActivatingPlayer(player);if(!spell.canPlay())throw new AssertionError("Control needs legal timing");
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",player.getId());row.addProperty("hook",player.getController().getClass().getName().replace('.','/')+".chooseSpellAbilityToPlay()Ljava/util/List;");row.addProperty("decision_type","priority_pass");row.addProperty("pass_return","null");row.addProperty("empty_mana_pool",true);
  JsonObject context=new JsonObject();context.addProperty("turn",phase.getTurn());context.addProperty("phase",String.valueOf(phase.getPhase()));context.addProperty("priority_player_id",player.getId());context.addProperty("turn_player_id",player.getId());row.add("context",context);
  if(mode.equals("wrong-context"))context.addProperty("turn",phase.getTurn()+1);
  if(mode.equals("wrong-priority"))phase.setPriority(game.getPlayers().get(1));
  JsonObject end=new JsonObject();end.addProperty("kind","decision_tape_complete");end.addProperty("decisions",1);Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n"+end+"\n",StandardOpenOption.CREATE_NEW);
  System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  if(mode.equals("pass")){
   if(player.getController().chooseSpellAbilityToPlay()!=null)throw new AssertionError("Recorded pass changed");DecisionReplay.finish();
   if(land.isTapped()||!bolt.isInZone(ZoneType.Hand)||!game.getStack().isEmpty())throw new AssertionError("Pass copied an outcome/mutated resources");
   System.out.println("PASS four-player recorded priority pass with castable spell available; resources and stack unchanged");
  }else{
   try{player.getController().chooseSpellAbilityToPlay();throw new AssertionError("Invalid pass accepted");}catch(IllegalStateException expected){if(!expected.getMessage().contains(mode.equals("wrong-context")?"context diverged":"does not hold priority"))throw expected;}
   if(!Files.exists(root.resolve("diagnostics/decision-failure-0.json")))throw new AssertionError("Missing reproducible rejection diagnostic");
   try{DecisionReplay.finish();throw new AssertionError("Failed replay completed");}catch(IllegalStateException expected){if(!expected.getMessage().contains("failed decision"))throw expected;}
   System.out.println("PASS four-player "+mode+" rejected, diagnostic retained, completion denied");
  }
  System.exit(0);
 }
}
