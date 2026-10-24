import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Two-process actual controller record/replay; bounded families only. */
public class DecisionReplayRegression extends AITest {
 static String hash(Path path)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));}
 static JsonObject prompt(String hook,Player p,SpellAbility sa,String title,int min,int max,int index){
  JsonObject row=new JsonObject();row.addProperty("kind","decision");row.addProperty("index",index);row.addProperty("hook",hook);row.addProperty("actor_id",p.getId());row.addProperty("source_ability",sa.getHostCard().getId()+":"+sa.getId());row.addProperty("title",title);row.addProperty("min",min);row.addProperty("max",max);return row;
 }
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);Path tape=root.resolve("decisions.jsonl");
  DecisionReplayRegression test=new DecisionReplayRegression();test.initializeModel();Game game=test.initAndCreateThreePlayerGame();Player player=game.getPlayers().get(1);
  for(Player p:game.getPlayers())test.fillLibrary(p,10);
  Card hydra=test.addCardToZone("Voracious Hydra",player,ZoneType.Hand);SpellAbility sa=hydra.getFirstSpellAbility();sa.setActivatingPlayer(player);
  Card first=test.addCard("Forest",player),second=test.addCard("Island",player);CardCollection offered=new CardCollection();offered.add(first);offered.add(second);
  String owner=player.getController().getClass().getName().replace('.','/');
  String numberHook=owner+".chooseNumber(Lforge/game/spellability/SpellAbility;Ljava/lang/String;II)I";
  String cardsHook=owner+".chooseCardsForEffect(Lforge/game/card/CardCollectionView;Lforge/game/spellability/SpellAbility;Ljava/lang/String;IIZLjava/util/Map;)Lforge/game/card/CardCollectionView;";
  if(!mode.equals("record")){System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",hash(tape));}
  if(mode.startsWith("reject-")){
   try{
    if(mode.equals("reject-card"))player.getController().chooseCardsForEffect(offered,sa,"live offered cards",1,1,false,Map.of());
    else player.getController().chooseNumber(sa,"bounded X choice",2,7);
    throw new AssertionError("Illegal choice was accepted");
   }catch(IllegalStateException expected){if(!expected.getMessage().startsWith("Illegal recorded"))throw expected;}
   try{DecisionReplay.finish();throw new AssertionError("Failed replay completed");}catch(IllegalStateException expected){if(!expected.getMessage().contains("failed decision"))throw expected;}
   System.out.println("PASS "+mode+": illegal recorded choice rejected; no AI fallback or completion");System.exit(0);
  }
  int number=player.getController().chooseNumber(sa,"bounded X choice",2,7);
  CardCollectionView chosen=player.getController().chooseCardsForEffect(offered,sa,"live offered cards",1,1,false,Map.of());
  if(mode.equals("record")){
   JsonObject a=prompt(numberHook,player,sa,"bounded X choice",2,7,0);a.addProperty("number",number);
   JsonObject b=prompt(cardsHook,player,sa,"live offered cards",1,1,1);b.addProperty("optional",false);JsonArray available=new JsonArray(),selected=new JsonArray();for(Card c:offered)available.add(c.getId());for(Card c:chosen)selected.add(c.getId());b.add("available_card_ids",available);b.add("selected_card_ids",selected);
   JsonObject end=new JsonObject();end.addProperty("kind","decision_tape_complete");end.addProperty("decisions",2);Files.writeString(tape,a+"\n"+b+"\n"+end+"\n",StandardOpenOption.CREATE_NEW);
   System.out.println("PASS recorded actual controller choices: number="+number+", selected="+selected+", owner="+owner+", sha256="+hash(tape));
  }else{
   List<String> rows=Files.readAllLines(tape);JsonObject a=JsonParser.parseString(rows.get(0)).getAsJsonObject(),b=JsonParser.parseString(rows.get(1)).getAsJsonObject();
   if(number!=a.get("number").getAsInt()||chosen.size()!=1||chosen.get(0).getId()!=b.getAsJsonArray("selected_card_ids").get(0).getAsInt())throw new AssertionError("Recorded choices changed");
   if(chosen.get(0)!=first&&chosen.get(0)!=second)throw new AssertionError("Card was not rebound to actual live offered object");DecisionReplay.finish();
   try{player.getController().chooseNumber(sa,"unsupported overload",0,3,Map.of());throw new AssertionError("Unsupported decision fell through to AI");}catch(IllegalStateException expected){if(!expected.getMessage().contains("Unsupported recorded decision"))throw expected;}
   try{DecisionReplay.finish();throw new AssertionError("Failed replay accepted completion");}catch(IllegalStateException expected){if(!expected.getMessage().contains("failed decision"))throw expected;}
   System.out.println("PASS recorded decisions drive actual controller with live card identity; unsupported overload rejects before AI; failure cannot complete");
  }
  System.exit(0);
 }
}
