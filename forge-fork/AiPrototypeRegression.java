import forge.ai.*;
import forge.ai.bridge.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.card.*;
import forge.game.card.token.TokenInfo;
import forge.game.player.*;
import forge.game.phase.*;
import forge.game.zone.*;
import forge.game.spellability.*;
import forge.game.ability.effects.TokenEffect;
import com.google.gson.*;
import java.nio.file.*;
import java.lang.reflect.Field;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

/** Actual four-player Talrand preview and real token paths; no complete-game claim. */
public final class AiPrototypeRegression extends AITest {
 public static void main(String[] args)throws Exception {
  String mode=args[0];boolean old=mode.equals("old");Path root=Path.of(args[1]);Files.createDirectories(root);
  System.setProperty("forge.audit.directory",root.resolve("audit").toString());
  AiPrototypeRegression test=new AiPrototypeRegression();test.initializeModel();test.initAndCreateGame();
  List<RegisteredPlayer> seats=new ArrayList<>();for(int i=0;i<4;i++)seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi("seat"+i,null)));
  GameRules rules=new GameRules(GameType.Commander);Game game=new Game(seats,rules,new Match(rules,seats,"Prototype identity"));Player player=game.getPlayers().get(0);
  for(Player p:game.getPlayers())test.fillLibrary(p,10);
  game.setAge(GameStage.Play);game.getPhaseHandler().devModeSet(PhaseType.MAIN1,player,false);game.getPhaseHandler().setPriority(player);
  Card source=test.addCardToZone("Talrand, Sky Summoner",player,ZoneType.Battlefield);
  SpellAbility ability=source.getTriggers().stream().filter(t->t.getOverridingAbility()!=null&&String.valueOf(t.getOverridingAbility().getApi()).equals("Token")).findFirst().orElseThrow().getOverridingAbility().copy();ability.setActivatingPlayer(player);
  Field liveCounter=Game.class.getDeclaredField("cardIdCounter"),hiddenCounter=Game.class.getDeclaredField("hiddenCardIdCounter");liveCounter.setAccessible(true);hiddenCounter.setAccessible(true);
  int before=liveCounter.getInt(game),hiddenBefore=hiddenCounter.getInt(game),battlefieldBefore=player.getCardsIn(ZoneType.Battlefield).size();
  DurableEvidence.begin("prototype-identity-fixture");EngineEvidence.begin(game);System.setProperty("forge.evidence.traceCardAllocation","true");
  JsonArray previews=new JsonArray();Set<Integer> ids=new HashSet<>();String previewColor=null;
  if(mode.equals("boundary")){
   liveCounter.setInt(game,999_999_999);hiddenCounter.setInt(game,999_999_999);
   try{game.nextCardId();throw new AssertionError("Live ID entered prototype range");}catch(IllegalStateException expected){if(!expected.getMessage().contains("disjoint identity range"))throw expected;}
   try{game.nextHiddenCardId();throw new AssertionError("Hidden ID entered prototype range");}catch(IllegalStateException expected){if(!expected.getMessage().contains("disjoint identity range"))throw expected;}
   // Restore only this deliberately modified boundary fixture, never a live game.
   liveCounter.setInt(game,before);hiddenCounter.setInt(game,hiddenBefore);
  }else if(mode.equals("invalid")){
   SpellAbility invalid=ability.copy();invalid.putParam("TokenScript","dragonmind_missing_token_script");
   try{forge.ai.ability.TokenAi.spawnToken(player,invalid);throw new AssertionError("Missing token script accepted");}catch(RuntimeException expected){/* factory scope must be restored */}
  }else if(mode.equals("exhaustion")){
   Field sequence=Class.forName("forge.ai.bridge.AiTokenPrototypes").getDeclaredField("sequence");sequence.setAccessible(true);((AtomicLong)sequence.get(null)).set(Integer.MAX_VALUE);
   try{forge.ai.ability.TokenAi.spawnToken(player,ability);throw new AssertionError("Exhausted private IDs reused");}catch(IllegalStateException expected){if(!expected.getMessage().contains("identity space exhausted"))throw expected;}
  }else{
   for(int i=0;i<6;i++){
    Card preview=forge.ai.ability.TokenAi.spawnToken(player,ability);
    if(!ids.add(preview.getId())||(!old&&preview.getId()<1_000_000_000)||!preview.isToken()||preview.getGame()!=game||preview.getOwner()!=player||preview.getController()!=player||preview.getNetPower()!=2||preview.getNetToughness()!=2||!preview.hasKeyword("Flying"))throw new AssertionError("Prototype wrong: id="+preview.getId()+" token="+preview.isToken()+" sameGame="+(preview.getGame()==game)+" owner="+preview.getOwner()+" controller="+preview.getController()+" PT="+preview.getNetPower()+"/"+preview.getNetToughness()+" flying="+preview.hasKeyword("Flying"));
    previewColor=preview.getColor().toString();JsonObject row=new JsonObject();row.addProperty("id",preview.getId());row.addProperty("name",preview.getName());row.addProperty("color",previewColor);previews.add(row);
   }
  }
  int afterPreviews=liveCounter.getInt(game);
  if(mode.equals("fixed")){
   for(int i=1;i<previews.size();i++)if(previews.get(i).getAsJsonObject().get("id").getAsInt()<=previews.get(i-1).getAsJsonObject().get("id").getAsInt())throw new AssertionError("Preview allocation ordering reversed");
   SpellAbility invalid=ability.copy();invalid.putParam("TokenScript","dragonmind_missing_token_script");
   try{forge.ai.ability.TokenAi.spawnToken(player,invalid);throw new AssertionError("Missing script accepted");}catch(RuntimeException expected){}
   Field sequence=Class.forName("forge.ai.bridge.AiTokenPrototypes").getDeclaredField("sequence");sequence.setAccessible(true);((AtomicLong)sequence.get(null)).set(Integer.MAX_VALUE);
   try{forge.ai.ability.TokenAi.spawnToken(player,ability);throw new AssertionError("Exhaustion accepted");}catch(IllegalStateException expected){if(!expected.getMessage().contains("identity space exhausted"))throw expected;}
   liveCounter.setInt(game,999_999_999);hiddenCounter.setInt(game,999_999_999);
   try{game.nextCardId();throw new AssertionError("Live ID collision accepted");}catch(IllegalStateException expected){if(!expected.getMessage().contains("disjoint identity range"))throw expected;}
   try{game.nextHiddenCardId();throw new AssertionError("Hidden ID collision accepted");}catch(IllegalStateException expected){if(!expected.getMessage().contains("disjoint identity range"))throw expected;}
   liveCounter.setInt(game,before);hiddenCounter.setInt(game,hiddenBefore);
  }
  if(afterPreviews-before!=(old?6:0)||hiddenCounter.getInt(game)!=hiddenBefore||player.getCardsIn(ZoneType.Battlefield).size()!=battlefieldBefore||!game.getStack().isEmpty())throw new AssertionError("Preview mutated live allocator, hidden allocator, battlefield or stack");
  // This direct native call is outside the AI scope, including after exceptions.
  Card realTemplate=TokenInfo.getProtoType(ability.getParam("TokenScript"),ability,player);
  if(realTemplate.getId()<=0||liveCounter.getInt(game)!=afterPreviews+1)throw new AssertionError("AI scope leaked into real token factory");
  new TokenEffect().resolve(ability);
  var tokens=player.getCardsIn(ZoneType.Battlefield).stream().filter(Card::isToken).toList();
  if(tokens.size()!=1)throw new AssertionError("Native token effect did not create exactly1 token");Card token=tokens.get(0);
  if(token.getId()<=0||token.getOwner()!=player||token.getController()!=player||token.getNetPower()!=2||token.getNetToughness()!=2||!token.hasKeyword("Flying")||!token.getName().equals(realTemplate.getName())||!token.getColor().equals(realTemplate.getColor())||(!old&&ids.contains(token.getId()))||(previewColor!=null&&!previewColor.equals(token.getColor().toString())))throw new AssertionError("Real token characteristics or identity changed");
  for(Player p:game.getPlayers())if(p!=player&&p.getCardsIn(ZoneType.Battlefield).stream().anyMatch(Card::isToken))throw new AssertionError("Wrong token recipient");
  System.setProperty("forge.evidence.traceCardAllocation","false");EngineEvidence.finish();
  JsonObject report=new JsonObject();report.addProperty("mode",mode);report.addProperty("preview_live_id_delta",afterPreviews-before);report.addProperty("hidden_allocator_unchanged",true);report.add("previews",previews);report.addProperty("real_template_id",realTemplate.getId());report.addProperty("real_token_id",token.getId());report.addProperty("real_token_owner",token.getOwner().getId());report.addProperty("real_token_controller",token.getController().getId());report.addProperty("real_token_name",token.getName());report.addProperty("real_token_color",token.getColor().toString());report.addProperty("full_game_approved",false);Files.writeString(root.resolve("result.json"),report+"\n",StandardOpenOption.CREATE_NEW);
  JsonObject result=new JsonObject();result.addProperty("seed",106);result.addProperty("status","completed");DurableEvidence.finish(root.resolve("results"),106,"fixture\nDragonMind Result: "+result+"\n",result);
  System.out.println("PASS four-player "+mode+": preview identity isolation and unchanged native token creation");System.exit(0);
 }
}
