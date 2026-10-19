package forge.ai.bridge;

import com.google.gson.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.replacement.ReplacementEffect;
import forge.card.ColorSet;
import forge.game.zone.ZoneType;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.security.*;

/** Bounded decision driver. Unsupported choices fail before invoking any AI.
 * Private referee input; never supplied to a learner or live pilot.
 */
public final class DecisionReplay {
 private static BufferedReader input;
 private static long consumed;
 private static boolean failed;
 private static MessageDigest readDigest;
 private static String boundHash;
 private DecisionReplay(){}
 public static boolean enabled(){return System.getProperty("forge.decision.replayTape")!=null;}
 private static void open()throws Exception {
  if(input!=null)return;
  Path path=Path.of(System.getProperty("forge.decision.replayTape"));
  MessageDigest digest=MessageDigest.getInstance("SHA-256");
  try(InputStream stream=Files.newInputStream(path)){byte[] b=new byte[65536];int n;while((n=stream.read(b))!=-1)digest.update(b,0,n);}
  String expected=System.getProperty("forge.decision.replaySha256");
  if(expected==null||!HexFormat.of().formatHex(digest.digest()).equals(expected))throw new IllegalStateException("Decision tape hash mismatch");
  boundHash=expected;readDigest=MessageDigest.getInstance("SHA-256");
  input=new BufferedReader(new InputStreamReader(new DigestInputStream(Files.newInputStream(path),readDigest),java.nio.charset.StandardCharsets.UTF_8));consumed=0;
 }
 private static String source(SpellAbility ability){return ability==null?null:ability.getHostCard().getId()+":"+ability.getId();}
 private static long integer(JsonElement value){
  if(value==null||!value.isJsonPrimitive()||!value.getAsJsonPrimitive().isNumber())throw new IllegalStateException("Non-numeric decision integer");
  try{return new java.math.BigDecimal(value.getAsString()).longValueExact();}catch(ArithmeticException e){throw new IllegalStateException("Non-integral/out-of-range decision integer",e);}
 }
 private static void diagnose(String hook,Object receiver,Exception failure){
  String directory=System.getProperty("forge.decision.replayDiagnostics");if(directory==null)return;
  try{
   Path root=Path.of(directory);Files.createDirectories(root);JsonObject row=new JsonObject();
   row.addProperty("decision_index",consumed);row.addProperty("hook",hook);row.addProperty("reason",failure.getMessage());
   if(receiver instanceof PlayerController controller)row.addProperty("actor_id",controller.getPlayer().getId());
   row.addProperty("rules_approved",false);Files.writeString(root.resolve("decision-failure-"+consumed+".json"),row+"\n",StandardOpenOption.CREATE_NEW);
  }catch(Exception evidenceFailure){failure.addSuppressed(evidenceFailure);}
 }
 private static void turnContext(JsonObject row,PlayerController controller){
  Player player=controller.getPlayer();var game=player.getGame();var phase=game.getPhaseHandler();JsonObject expected=row.getAsJsonObject("context");
  if(player.hasLost()||!game.getPlayers().contains(player)||phase.getPriorityPlayer()!=player)throw new IllegalStateException("Illegal priority pass: actor does not hold priority");
  if(expected==null||integer(expected.get("turn"))!=phase.getTurn()||!expected.get("phase").getAsString().equals(String.valueOf(phase.getPhase()))||integer(expected.get("priority_player_id"))!=player.getId()||phase.getPlayerTurn()==null||integer(expected.get("turn_player_id"))!=phase.getPlayerTurn().getId())throw new IllegalStateException("Priority replay context diverged");
  if(!Set.of("UPKEEP","DRAW","MAIN1","COMBAT_BEGIN","COMBAT_DECLARE_ATTACKERS","COMBAT_DECLARE_BLOCKERS","COMBAT_FIRST_STRIKE_DAMAGE","COMBAT_DAMAGE","COMBAT_END","MAIN2","END_OF_TURN").contains(String.valueOf(phase.getPhase())))throw new IllegalStateException("Unsupported priority step");
 }
 private static void priorityContext(JsonObject row,PlayerController controller){turnContext(row,controller);Player player=controller.getPlayer();if(!row.has("empty_mana_pool")||!row.get("empty_mana_pool").getAsJsonPrimitive().isBoolean()||!row.get("empty_mana_pool").getAsBoolean()||!player.getManaPool().isEmpty())throw new IllegalStateException("Priority pass with mana requires public announcement support");}
 private static JsonObject traitIdentity(ReplacementEffect effect){
  JsonObject row=new JsonObject();row.addProperty("trait_type",effect.getClass().getName());row.addProperty("source_card_id",effect.getHostCard().getId());JsonObject params=new JsonObject();effect.getMapParams().forEach(params::addProperty);row.add("parameters",params);return row;
 }
 private static Object complete(String hook,Object receiver,Object[] args,Object result){long token=EngineEvidence.enter(hook,receiver,args);EngineEvidence.leave(token,result);consumed++;return result;}
 private static void bindAbility(JsonObject row,SpellAbility ability){JsonElement expected=row.get("source_ability");if(expected==null||!Objects.equals(expected.isJsonNull()?null:expected.getAsString(),source(ability)))throw new IllegalStateException("Effect source ability diverged");}
 public static synchronized Object invoke(String hook,Object receiver,Object[] args) {
  if(failed)throw new IllegalStateException("Decision replay already failed");
  boolean number=hook.endsWith(".chooseNumber(Lforge/game/spellability/SpellAbility;Ljava/lang/String;II)I");
  boolean cards=hook.endsWith(".chooseCardsForEffect(Lforge/game/card/CardCollectionView;Lforge/game/spellability/SpellAbility;Ljava/lang/String;IIZLjava/util/Map;)Lforge/game/card/CardCollectionView;");
  boolean priority=hook.endsWith(".chooseSpellAbilityToPlay()Ljava/util/List;");
  boolean replacement=hook.endsWith(".chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;");
  boolean counter=hook.endsWith(".chooseCounterType(Ljava/util/List;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Ljava/util/Map;)Lforge/game/card/CounterType;");
  boolean colors=hook.endsWith(".chooseColors(Ljava/lang/String;Lforge/game/spellability/SpellAbility;IILforge/card/ColorSet;)Lforge/card/ColorSet;");
  boolean start=hook.endsWith(".chooseStartingPlayer(Z)Lforge/game/player/Player;");
  boolean mulligan=hook.endsWith(".mulliganKeepHand(Lforge/game/player/Player;I)Z");
  try {
   if(!number&&!cards&&!priority&&!replacement&&!counter&&!colors&&!start&&!mulligan)throw new IllegalStateException("Unsupported recorded decision: "+hook);
   if(!(receiver instanceof PlayerController controller))throw new IllegalStateException("Missing controller");
   open();String line=input.readLine();if(line==null)throw new IllegalStateException("Decision tape exhausted");
   JsonObject row=JsonParser.parseString(line).getAsJsonObject();
   if("unsupported_decision".equals(row.get("kind").getAsString()))throw new IllegalStateException("Unsupported recorded decision row: "+row.get("reason"));
   if(!row.get("kind").getAsString().equals("decision")||integer(row.get("index"))!=consumed||!row.get("hook").getAsString().equals(hook)||integer(row.get("actor_id"))!=controller.getPlayer().getId())throw new IllegalStateException("Decision order/actor/hook diverged");
   if(start||mulligan){
    Player player=controller.getPlayer();var game=player.getGame();if(game.getPhaseHandler().getTurn()!=0||game.getPhaseHandler().getPhase()!=null||player.hasLost())throw new IllegalStateException("Illegal pregame decision context");
    if(start){
     if(!row.get("first_game").getAsJsonPrimitive().isBoolean()||row.get("first_game").getAsBoolean()!=(Boolean)args[0])throw new IllegalStateException("Starting player prompt diverged");
     JsonArray eligible=new JsonArray();Player selected=null;for(Player candidate:game.getPlayers()){eligible.add(candidate.getId());if(candidate.getId()==integer(row.get("selected_player_id")))selected=candidate;}
     if(!eligible.equals(row.get("eligible_player_ids"))||selected==null||selected.hasLost())throw new IllegalStateException("Illegal recorded starting player");return complete(hook,receiver,args,selected);
    }
    if(!(args[0] instanceof Player first)||first.getGame()!=game||first.getId()!=integer(row.get("starting_player_id"))||integer(row.get("mulligan_count"))!=(Integer)args[1]||(Integer)args[1]<0||!row.get("keep").getAsJsonPrimitive().isBoolean())throw new IllegalStateException("Mulligan prompt diverged");
    boolean keep=row.get("keep").getAsBoolean();if(!keep&&(!player.canMulligan()||player.getCardsIn(ZoneType.Hand).isEmpty()))throw new IllegalStateException("Illegal mulligan of empty/ineligible hand");return complete(hook,receiver,args,keep);
   }
   if(priority){
    if(args.length==0&&"play_land".equals(row.get("decision_type").getAsString())){
     turnContext(row,controller);Player player=controller.getPlayer();var game=player.getGame();String phase=String.valueOf(game.getPhaseHandler().getPhase());
     if(game.getPhaseHandler().getPlayerTurn()!=player||!game.getStack().isEmpty()||!(phase.equals("MAIN1")||phase.equals("MAIN2")))throw new IllegalStateException("Illegal land special-action timing");
     Card selected=null;for(Card card:player.getCardsIn(ZoneType.Hand))if(card.getId()==integer(row.get("land_card_id"))){if(selected!=null)throw new IllegalStateException("Ambiguous live land object");selected=card;}
     if(selected==null||!selected.isLand()||selected.getOwner()!=player||selected.getOwner().getId()!=integer(row.get("land_owner_id"))||!selected.getName().equals(row.get("land_name").getAsString()))throw new IllegalStateException("Illegal recorded hand land");
     LandAbility land=new LandAbility(selected,selected.getCurrentState());land.setActivatingPlayer(player);if(!land.canPlay())throw new IllegalStateException("Illegal land play limit or restriction");return complete(hook,receiver,args,Collections.singletonList(land));
    }
    if(args.length!=0||!"priority_pass".equals(row.get("decision_type").getAsString()))throw new IllegalStateException("Unsupported priority selection");
    priorityContext(row,controller);String kind=row.get("pass_return").getAsString();Object result;
    if(kind.equals("null"))result=null;else if(kind.equals("empty_list"))result=Collections.emptyList();else throw new IllegalStateException("Invalid priority pass encoding");
    return complete(hook,receiver,args,result);
   }
   if(replacement){
    if(!"replacement_choice".equals(row.get("decision_type").getAsString()))throw new IllegalStateException("Wrong replacement decision type");
    JsonArray offered=new JsonArray();List<ReplacementEffect> live=new ArrayList<>();
    for(Object value:(List<?>)args[0]){ReplacementEffect effect=(ReplacementEffect)value;JsonObject identity=traitIdentity(effect);for(JsonElement prior:offered)if(prior.equals(identity))throw new IllegalStateException("Ambiguous replacement identity");live.add(effect);offered.add(identity);}
    if(!offered.equals(row.get("available_effects")))throw new IllegalStateException("Replacement legal domain diverged");
    ReplacementEffect selected=null;for(ReplacementEffect effect:live)if(traitIdentity(effect).equals(row.get("selected_effect")))selected=effect;
    if(selected==null||selected.hasRun()||!selected.requirementsCheck(controller.getPlayer().getGame()))throw new IllegalStateException("Illegal recorded replacement choice");
    return complete(hook,receiver,args,selected);
   }
   if(counter){
    bindAbility(row,(SpellAbility)args[1]);if(!row.get("title").getAsString().equals(args[2]))throw new IllegalStateException("Counter prompt diverged");
    JsonArray offered=new JsonArray();Map<String,CounterType> live=new LinkedHashMap<>();for(Object item:(List<?>)args[0]){if(!(item instanceof CounterType type)||!(item instanceof Enum<?>))throw new IllegalStateException("Unsupported custom counter identity");String id=item.toString();if(live.put(id,type)!=null)throw new IllegalStateException("Ambiguous counter identity");offered.add(id);}
    if(!offered.equals(row.get("available_counters")))throw new IllegalStateException("Counter legal domain diverged");
    Map<?,?> params=(Map<?,?>)args[3];JsonArray keys=new JsonArray();List<String> sorted=new ArrayList<>();for(var entry:params.entrySet()){if(entry.getValue()!=null)throw new IllegalStateException("Unsupported non-null counter parameter");sorted.add((String)entry.getKey());}Collections.sort(sorted);sorted.forEach(keys::add);
    if(!keys.equals(row.get("null_parameter_keys")))throw new IllegalStateException("Counter parameters diverged");CounterType selected=live.get(row.get("selected_counter").getAsString());if(selected==null)throw new IllegalStateException("Illegal recorded counter choice");return complete(hook,receiver,args,selected);
   }
   if(colors){
    bindAbility(row,(SpellAbility)args[1]);ColorSet allowed=(ColorSet)args[4];
    if(!row.get("title").getAsString().equals(args[0])||integer(row.get("min"))!=(Integer)args[2]||integer(row.get("max"))!=(Integer)args[3]||!allowed.toString().equals(row.get("allowed_colors").getAsString()))throw new IllegalStateException("Color prompt/domain diverged");
    ColorSet selected=ColorSet.valueOf(row.get("selected_colors").getAsString());int count=Integer.bitCount(selected.getColor());
    if(!selected.hasNoColorsExcept(allowed)||count<(Integer)args[2]||count>(Integer)args[3])throw new IllegalStateException("Illegal recorded color choice");return complete(hook,receiver,args,selected);
   }
   int offset=number?0:1;SpellAbility ability=(SpellAbility)args[offset];String title=(String)args[offset+1];
   JsonElement binding=row.get("source_ability");
   if(binding==null||!Objects.equals(binding.isJsonNull()?null:binding.getAsString(),source(ability))||!row.get("title").getAsString().equals(title))throw new IllegalStateException("Decision prompt/source diverged");
   int min=(Integer)args[offset+2],max=(Integer)args[offset+3];
   if(integer(row.get("min"))!=min||integer(row.get("max"))!=max)throw new IllegalStateException("Decision bounds diverged");
   Object result;
   if(number) {
    long n=integer(row.get("number"));if(n<min||n>max)throw new IllegalStateException("Illegal recorded number");result=(int)n;
   }else {
    boolean optional=(Boolean)args[5];if(row.get("optional").getAsBoolean()!=optional)throw new IllegalStateException("Optional choice diverged");
    Map<Integer,Card> available=new LinkedHashMap<>();JsonArray ids=new JsonArray();
    for(Card card:(CardCollectionView)args[0]){if(available.put(card.getId(),card)!=null)throw new IllegalStateException("Ambiguous live card ID");ids.add(card.getId());}
    if(!ids.equals(row.get("available_card_ids")))throw new IllegalStateException("Legal option inventory diverged");
    CardCollection selected=new CardCollection();Set<Integer> seen=new HashSet<>();
    for(JsonElement value:row.getAsJsonArray("selected_card_ids")){int id=Math.toIntExact(integer(value));Card card=available.get(id);if(card==null||!seen.add(id))throw new IllegalStateException("Illegal recorded card choice");selected.add(card);}
    if(selected.size()>max||(selected.size()<min&&!(optional&&selected.isEmpty())))throw new IllegalStateException("Illegal recorded card count");
    result=selected;
   }
   return complete(hook,receiver,args,result);
  }catch(RuntimeException e){failed=true;diagnose(hook,receiver,e);throw e;}catch(Exception e){failed=true;diagnose(hook,receiver,e);throw new IllegalStateException("Decision replay failed",e);}
 }
 public static synchronized void finish()throws Exception {
  if(failed)throw new IllegalStateException("Cannot complete failed decision replay");
  if(input==null)throw new IllegalStateException("No recorded decisions consumed");
  try {
   String line=input.readLine();if(line==null)throw new IllegalStateException("Missing decision completion marker");
   JsonObject row=JsonParser.parseString(line).getAsJsonObject();
   if(!row.get("kind").getAsString().equals("decision_tape_complete")||integer(row.get("decisions"))!=consumed||input.readLine()!=null)throw new IllegalStateException("Unconsumed/incomplete decision tape");
   if(!HexFormat.of().formatHex(readDigest.digest()).equals(boundHash))throw new IllegalStateException("Decision input changed after hash verification");
  }catch(Exception e){failed=true;throw e;}finally{input.close();input=null;}
 }
}
