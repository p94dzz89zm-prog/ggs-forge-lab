import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import forge.model.FModel;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Actual pregame choices and legal land execution, never post-state copying. */
public class InitialLandReplayRegression extends AITest {
 static JsonObject row(Player p,String hook,int index,String type){JsonObject r=new JsonObject();r.addProperty("kind","decision");r.addProperty("hook",p.getController().getClass().getName().replace('.','/')+hook);r.addProperty("actor_id",p.getId());r.addProperty("index",index);r.addProperty("decision_type",type);return r;}
 static JsonObject land(Player player,Card card,int index){JsonObject r=row(player,".chooseSpellAbilityToPlay()Ljava/util/List;",index,"play_land");r.addProperty("land_card_id",card.getId());r.addProperty("land_owner_id",player.getId());r.addProperty("land_name",card.getName());var ph=player.getGame().getPhaseHandler();JsonObject c=new JsonObject();c.addProperty("turn",ph.getTurn());c.addProperty("phase",String.valueOf(ph.getPhase()));c.addProperty("priority_player_id",player.getId());c.addProperty("turn_player_id",player.getId());r.add("context",c);return r;}
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);InitialLandReplayRegression test=new InitialLandReplayRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));GameRules rules=new GameRules(GameType.Constructed);Game game=new Game(seats,rules,new Match(rules,seats,"Initial and land replay"));Player p=game.getPlayers().get(0);for(Player x:game.getPlayers())test.fillLibrary(x,10);
  boolean isLand=mode.startsWith("land");List<JsonObject> rows=new ArrayList<>();Card first=null,second=null;
  if(isLand){game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false);game.getPhaseHandler().setPriority(p);first=test.addCardToZone("Command Tower",p,ZoneType.Hand);second=test.addCardToZone("Island",p,ZoneType.Hand);rows.add(land(p,first,0));if(mode.equals("land-limit"))rows.add(land(p,second,1));}
  else{
   if(!mode.equals("bad-mulligan"))for(int i=0;i<7;i++)test.addCardToZone("Forest",p,ZoneType.Hand);
   JsonObject start=row(p,".chooseStartingPlayer(Z)Lforge/game/player/Player;",0,"starting_player");start.addProperty("first_game",true);JsonArray ids=new JsonArray();for(Player x:game.getPlayers())ids.add(x.getId());start.add("eligible_player_ids",ids);start.addProperty("selected_player_id",mode.equals("bad-start")?999999:game.getPlayers().get(2).getId());rows.add(start);
   JsonObject keep=row(p,".mulliganKeepHand(Lforge/game/player/Player;I)Z",1,"mulligan_keep");keep.addProperty("starting_player_id",game.getPlayers().get(2).getId());keep.addProperty("mulligan_count",0);keep.addProperty("keep",false);rows.add(keep);
  }
  JsonObject end=new JsonObject();end.addProperty("kind","decision_tape_complete");end.addProperty("decisions",rows.size());StringBuilder content=new StringBuilder();rows.forEach(r->content.append(r).append('\n'));content.append(end).append('\n');Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,content.toString(),StandardOpenOption.CREATE_NEW);System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try{
   if(isLand){
    List<SpellAbility> selected=p.getController().chooseSpellAbilityToPlay();if(selected.size()!=1||!selected.get(0).isLandAbility()||selected.get(0).getHostCard()!=first)throw new AssertionError("Land not live bound");if(!p.getController().playChosenSpellAbility(selected.get(0)))throw new AssertionError("Engine rejected chosen land");if(!first.isInZone(ZoneType.Battlefield)||p.getLandsPlayedThisTurn()!=1)throw new AssertionError("Engine did not execute legal land action");
    if(mode.equals("land-limit")){p.getController().chooseSpellAbilityToPlay();throw new AssertionError("Second land accepted");}
    if(args.length>2){int checked=0;for(String text:Files.readAllLines(Path.of(args[2]))){JsonObject r=JsonParser.parseString(text).getAsJsonObject();if(r.has("decision_type")&&r.get("decision_type").getAsString().equals("play_land")){String name=r.get("land_name").getAsString();if(!FModel.getMagicDb().getCommonCards().getCard(name).getRules().getType().isLand())throw new AssertionError("Original candidate is not land: "+name);checked++;}}if(checked!=32)throw new AssertionError("Expected32 original land types");System.out.println("PASS32 original selected land names independently checked against pinned card types");}
   }else{
    if(p.getController().chooseStartingPlayer(true)!=game.getPlayers().get(2))throw new AssertionError("Starting player not live rebound");if(p.getController().mulliganKeepHand(game.getPlayers().get(2),0))throw new AssertionError("Recorded reshuffle changed");if(p.getCardsIn(ZoneType.Hand).size()!=7)throw new AssertionError("Decision driver moved cards instead of returning choice");
   }
   if(!mode.equals("land-valid")&&!mode.equals("initial-valid"))throw new AssertionError("Invalid choice accepted");DecisionReplay.finish();System.out.println("PASS four-player "+mode+": recorded choice driven and legal engine execution verified");
  }catch(IllegalStateException failure){
   if(mode.equals("land-valid")||mode.equals("initial-valid"))throw failure;
   String expected=mode.equals("bad-start")?"starting player":mode.equals("bad-mulligan")?"empty/ineligible":"land play limit";if(!failure.getMessage().contains(expected))throw failure;
   try{DecisionReplay.finish();throw new AssertionError("Failure completed");}catch(IllegalStateException denied){if(!denied.getMessage().contains("failed decision"))throw denied;}
   System.out.println("PASS four-player "+mode+" rejected; no illegal state transition");
  }
  System.exit(0);
 }
}
