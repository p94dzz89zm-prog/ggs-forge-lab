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

/** Actual live spell selection, distinct from casting/payment approval. */
public class CommanderSelectionRegression extends AITest {
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);CommanderSelectionRegression test=new CommanderSelectionRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Plain spell selection"));Player p=game.getPlayers().get(0);
  game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);Card card=test.addCardToZone(mode.equals("wrong-type")?"Island":"Frodo, Adventurous Hobbit",p,mode.equals("missing")?ZoneType.Graveyard:ZoneType.Command);
  p.addCommander(card);game.getAction().checkStaticAbilities();
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",0);row.addProperty("actor_id",p.getId());row.addProperty("hook",p.getController().getClass().getName().replace('.','/')+".chooseSpellAbilityToPlay()Ljava/util/List;");row.addProperty("decision_type","command_permanent_spell");row.addProperty("source_card_id",card.getId());row.addProperty("source_name",card.getName());row.addProperty("mana_cost",card.getManaCost().toString());row.addProperty("selected_api","PermanentCreature");row.addProperty("prior_commander_casts",mode.equals("wrong-count")?1:0);row.addProperty("commander_tax",mode.equals("wrong-count")?2:0);
  JsonObject context=new JsonObject();context.addProperty("turn",game.getPhaseHandler().getTurn());context.addProperty("phase","MAIN1");context.addProperty("priority_player_id",p.getId());context.addProperty("turn_player_id",p.getId());row.add("context",context);
  Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,row+"\n{\"kind\":\"decision_tape_complete\",\"decisions\":1}\n",StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try{
   var selected=p.getController().chooseSpellAbilityToPlay();if(!mode.equals("valid"))throw new AssertionError("Invalid source accepted");if(selected.size()!=1||selected.get(0).getHostCard()!=card||selected.get(0).getMayPlayOption()==null||!card.isInZone(ZoneType.Command)||!game.getStack().isEmpty())throw new AssertionError("Spell selection copied cast outcome instead of binding live object");DecisionReplay.finish();System.out.println("PASS four-player live commander permission selected; no cast/payment outcome copied");
  }catch(IllegalStateException failure){
   if(mode.equals("valid"))throw failure;
   if(!failure.getMessage().contains(mode.equals("missing")?"spell source":"cast count"))throw failure;
   try{DecisionReplay.finish();throw new AssertionError("Failed choice completed");}catch(IllegalStateException denied){if(!denied.getMessage().contains("failed decision"))throw denied;}
   System.out.println("PASS four-player "+mode+" spell source rejected");
  }
  System.exit(0);
 }
}
