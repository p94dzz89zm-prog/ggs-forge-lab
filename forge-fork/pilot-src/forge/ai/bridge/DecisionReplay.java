package forge.ai.bridge;

import com.google.gson.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.replacement.ReplacementEffect;
import forge.card.ColorSet;
import forge.game.zone.ZoneType;
import forge.game.cost.*;
import forge.game.mana.ManaCostBeingPaid;
import forge.game.mana.Mana;
import forge.card.MagicColor;
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
 private static BufferedReader randomInput;
 private static MessageDigest randomDigest;
 private static String randomHash;
 private static long randomConsumed;
 private static JsonObject activeManaColor;
 private static SpellAbility activeManaAbility;
 private static final Map<String,String> selectedAbilityBindings=new HashMap<>();
 private static SpellAbility activeTriggerPayment;
 private static int triggerPayments;
 private static final Set<SpellAbility> boundTriggerInnerAbilities=Collections.newSetFromMap(new IdentityHashMap<>());
 private static String produced(SpellAbility ability,JsonObject step){return step.has("color_choice")?step.getAsJsonObject("color_choice").get("selected_color").getAsString():ability.getParam("Produced");}
 private DecisionReplay(){}
 public static boolean enabled(){return System.getProperty("forge.decision.replayTape")!=null;}
 public static synchronized int engineRandom(int bits,int generated){
  String file=System.getProperty("forge.decision.engineRandomTape");if(file==null)return generated;
  try{
   if(!enabled()||System.getProperty("forge.referee.replayTape")!=null||failed)throw new IllegalStateException("Incompatible or failed decision RNG replay");
   if(randomInput==null){
    randomHash=System.getProperty("forge.decision.engineRandomSha256");MessageDigest check=MessageDigest.getInstance("SHA-256");
    try(InputStream stream=Files.newInputStream(Path.of(file))){byte[] b=new byte[65536];int n;while((n=stream.read(b))!=-1)check.update(b,0,n);}
    if(randomHash==null||!HexFormat.of().formatHex(check.digest()).equals(randomHash))throw new IllegalStateException("Engine RNG tape hash mismatch");
    randomDigest=MessageDigest.getInstance("SHA-256");randomInput=new BufferedReader(new InputStreamReader(new DigestInputStream(Files.newInputStream(Path.of(file)),randomDigest),java.nio.charset.StandardCharsets.UTF_8));
   }
   String line=randomInput.readLine();JsonObject row=line==null?null:JsonParser.parseString(line).getAsJsonObject();
   if(row==null||!"engine_random_bits".equals(row.get("kind").getAsString())||integer(row.get("index"))!=randomConsumed||integer(row.get("bits"))!=bits)throw new IllegalStateException("Engine RNG request diverged at "+randomConsumed);
   long value=integer(row.get("value"));if(bits<1||bits>32||value<(bits==32?Integer.MIN_VALUE:0)||value>=(bits==32?1L<<31:1L<<bits))throw new IllegalStateException("Engine RNG value out of range");
   randomConsumed++;return (int)value;
  }catch(Exception e){failed=true;diagnose("engine_random",null,e);throw new IllegalStateException("Decision engine RNG failed",e);}
 }
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
   row.addProperty("engine_random_requests_consumed",randomConsumed);
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
 private static JsonArray poolInventory(Player player){JsonArray result=new JsonArray();for(Mana mana:player.getManaPool()){JsonObject unit=new JsonObject();unit.addProperty("color",MagicColor.toShortString(mana.getColor()));unit.addProperty("source_card_id",mana.getSourceCard().getId());unit.addProperty("snow",mana.isSnow());unit.addProperty("restricted",mana.isRestricted());result.add(unit);}return result;}
 private static void priorityContext(JsonObject row,PlayerController controller){turnContext(row,controller);Player player=controller.getPlayer();if(!row.has("empty_mana_pool")||!row.get("empty_mana_pool").getAsJsonPrimitive().isBoolean())throw new IllegalStateException("Missing mana pool expectation");if(row.get("empty_mana_pool").getAsBoolean()){if(!player.getManaPool().isEmpty())throw new IllegalStateException("Unexpected floating mana");}else if(!poolInventory(player).equals(row.get("expected_pool")))throw new IllegalStateException("Priority floating mana inventory diverged");}
 private static JsonObject traitIdentity(ReplacementEffect effect){
  JsonObject row=new JsonObject();row.addProperty("trait_type",effect.getClass().getName());row.addProperty("source_card_id",effect.getHostCard().getId());JsonObject params=new JsonObject();effect.getMapParams().forEach(params::addProperty);row.add("parameters",params);return row;
 }
 private static Object complete(String hook,Object receiver,Object[] args,Object result){long token=EngineEvidence.enter(hook,receiver,args);EngineEvidence.leave(token,result);consumed++;return result;}
 private static void bindAbility(JsonObject row,SpellAbility ability){JsonElement expected=row.get("source_ability");if(expected==null)throw new IllegalStateException("Missing effect source identity");String id=expected.isJsonNull()?null:expected.getAsString();if(!Objects.equals(selectedAbilityBindings.getOrDefault(id,id),source(ability))){JsonObject params=new JsonObject();if(ability!=null)ability.getMapParams().forEach(params::addProperty);if(ability==null||!boundTriggerInnerAbilities.contains(ability)||id==null||!id.startsWith(ability.getHostCard().getId()+":")||!row.has("ability_parameters")||!params.equals(row.get("ability_parameters"))||!String.valueOf(ability.getApi()).equals(row.get("ability_api").getAsString()))throw new IllegalStateException("Effect source ability diverged");String prior=selectedAbilityBindings.putIfAbsent(id,source(ability));if(prior!=null&&!prior.equals(source(ability)))throw new IllegalStateException("Ambiguous underlying trigger identity");}}
 public static synchronized Object invoke(String hook,Object receiver,Object[] args) {
  if(failed)throw new IllegalStateException("Decision replay already failed");
  if(activeTriggerPayment!=null&&hook.endsWith(".payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z")){
   try{if(args[1]!=activeTriggerPayment||args[2]!=null||args[3]!=null||!Boolean.FALSE.equals(args[4])||!(receiver instanceof PlayerController pc)||pc.getPlayer()!=activeTriggerPayment.getActivatingPlayer()||!(args[0] instanceof CostPartMana part)||part.getAmountOfX()!=0||!part.getManaCostFor(activeTriggerPayment).isZero())throw new IllegalStateException("Nested trigger payment differs");ManaCostBeingPaid zero=new ManaCostBeingPaid(part.getManaCostFor(activeTriggerPayment));CostAdjustment.adjust(zero,activeTriggerPayment,pc.getPlayer(),null,false,false);if(!zero.isPaid())throw new IllegalStateException("Trigger adjusted payment is not zero");long token=EngineEvidence.enter(hook,receiver,args);EngineEvidence.leave(token,true);triggerPayments++;return true;}catch(RuntimeException error){failed=true;throw error;}
  }
  if(activeManaColor!=null){
   try{JsonObject color=activeManaColor;if(!hook.equals(color.get("hook").getAsString())||args.length!=3||args[1]!=activeManaAbility||!Objects.equals(args[0],color.get("title").getAsString())||!args[2].toString().equals(color.get("offered").getAsString())||!(receiver instanceof PlayerController pc)||pc.getPlayer()!=activeManaAbility.getActivatingPlayer())throw new IllegalStateException("Nested mana color context diverged");byte selected=(byte)integer(color.get("selected_mask"));if(Integer.bitCount(Byte.toUnsignedInt(selected))!=1||!((ColorSet)args[2]).hasAnyColor(selected)||!MagicColor.toShortString(selected).equals(color.get("selected_color").getAsString()))throw new IllegalStateException("Illegal nested mana color");activeManaColor=null;long token=EngineEvidence.enter(hook,receiver,args);EngineEvidence.leave(token,selected);return selected;}catch(RuntimeException error){failed=true;throw error;}
  }
  boolean number=hook.endsWith(".chooseNumber(Lforge/game/spellability/SpellAbility;Ljava/lang/String;II)I");
  boolean cards=hook.endsWith(".chooseCardsForEffect(Lforge/game/card/CardCollectionView;Lforge/game/spellability/SpellAbility;Ljava/lang/String;IIZLjava/util/Map;)Lforge/game/card/CardCollectionView;");
  boolean priority=hook.endsWith(".chooseSpellAbilityToPlay()Ljava/util/List;");
  boolean replacement=hook.endsWith(".chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;");
  boolean counter=hook.endsWith(".chooseCounterType(Ljava/util/List;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Ljava/util/Map;)Lforge/game/card/CounterType;");
  boolean colors=hook.endsWith(".chooseColors(Ljava/lang/String;Lforge/game/spellability/SpellAbility;IILforge/card/ColorSet;)Lforge/card/ColorSet;");
  boolean start=hook.endsWith(".chooseStartingPlayer(Z)Lforge/game/player/Player;");
  boolean mulligan=hook.endsWith(".mulliganKeepHand(Lforge/game/player/Player;I)Z");
  boolean payment=hook.endsWith(".payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z");
  boolean triggerStack=hook.endsWith(".orderAndPlaySimultaneousSa(Ljava/util/List;)V");
  boolean singlePlayer=hook.endsWith(".chooseSingleEntityForEffect(Lforge/util/collect/FCollectionView;Lforge/game/player/DelayedReveal;Lforge/game/spellability/SpellAbility;Ljava/lang/String;ZLforge/game/player/Player;Ljava/util/Map;)Lforge/game/GameEntity;");
  try {
   if(!number&&!cards&&!priority&&!replacement&&!counter&&!colors&&!start&&!mulligan&&!payment&&!triggerStack&&!singlePlayer)throw new IllegalStateException("Unsupported recorded decision: "+hook);
   if(!(receiver instanceof PlayerController controller))throw new IllegalStateException("Missing controller");
   open();String line=input.readLine();if(line==null)throw new IllegalStateException("Decision tape exhausted");
   JsonObject row=JsonParser.parseString(line).getAsJsonObject();
   if("unsupported_decision".equals(row.get("kind").getAsString()))throw new IllegalStateException("Unsupported recorded decision row: "+row.get("reason"));
   if(!row.get("kind").getAsString().equals("decision")||integer(row.get("index"))!=consumed||!row.get("hook").getAsString().equals(hook)||integer(row.get("actor_id"))!=controller.getPlayer().getId())throw new IllegalStateException("Decision order/actor/hook diverged");
   if(singlePlayer){
    if(!row.get("decision_type").getAsString().equals("single_player_effect")||args.length!=7||args[1]!=null||args[5]!=null||args[6]!=null||!Objects.equals(args[3],row.get("title").getAsString())||!Objects.equals(args[4],row.get("optional").getAsBoolean()))throw new IllegalStateException("Unsupported player choice prompt/reveal/context");
    SpellAbility ability=(SpellAbility)args[2];bindAbility(row,ability);JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);if(!params.equals(row.get("ability_parameters"))||!String.valueOf(ability.getApi()).equals(row.get("ability_api").getAsString()))throw new IllegalStateException("Player choice source parameters diverged");
    JsonArray ids=new JsonArray();Map<Integer,Player> offered=new LinkedHashMap<>();for(Object item:(Iterable<?>)args[0]){if(!(item instanceof Player player)||player.hasLost()||player.getGame()!=controller.getPlayer().getGame()||offered.put(player.getId(),player)!=null)throw new IllegalStateException("Invalid offered player domain");ids.add(player.getId());}
    if(!ids.equals(row.get("available_player_ids")))throw new IllegalStateException("Player choice legal domain diverged");JsonElement chosen=row.get("selected_player_id");Player selected=chosen.isJsonNull()?null:offered.get(Math.toIntExact(integer(chosen)));if(selected==null&&(!chosen.isJsonNull()||!row.get("optional").getAsBoolean()))throw new IllegalStateException("Unavailable selected player");return complete(hook,receiver,args,selected);
   }
   if(triggerStack){
    if(!row.get("decision_type").getAsString().equals("partner_trigger_stack")||args.length!=1||!(args[0] instanceof List<?> offered)||offered.size()!=1||!(offered.get(0) instanceof forge.game.trigger.WrappedAbility wrapper))throw new IllegalStateException("Unsupported simultaneous trigger domain");
    Player player=controller.getPlayer();var game=player.getGame();Card card=wrapper.getHostCard();SpellAbility inner=wrapper.getWrappedAbility();
    if(card.getId()!=integer(row.get("source_card_id"))||!card.getName().equals(row.get("source_name").getAsString())||!Set.of("Frodo, Adventurous Hobbit","Sam, Loyal Attendant").contains(card.getName())||wrapper.getActivatingPlayer()!=player||!wrapper.isTrigger()||wrapper.isSpell()||wrapper.isCopied()||!String.valueOf(inner.getApi()).equals("ChangeZone")||inner.getSubAbility()!=null||inner.getPayCosts()==null||!inner.getPayCosts().isOnlyManaCost()||!inner.getPayCosts().getTotalMana().isZero()||inner.getXManaCostPaid()!=null||!inner.getTargets().isEmpty())throw new IllegalStateException("Partner trigger identity or preparation differs");
    String partner=card.getName().equals("Frodo, Adventurous Hobbit")?"Card.namedSam; Loyal Attendant":"Card.namedFrodo; Adventurous Hobbit";
    if(!inner.getMapParams().equals(Map.of("DB","ChangeZone","Origin","Library","Destination","Hand","Chooser","Targeted","Optional","True","ChangeType",partner,"ValidTgts","Player","Hidden","True")))throw new IllegalStateException("Unsupported partner trigger definition");
    JsonArray targets=row.getAsJsonArray("target_player_ids");if(targets.size()!=1)throw new IllegalStateException("Illegal partner target count");Player target=null;for(Player candidate:game.getPlayers())if(candidate.getId()==integer(targets.get(0)))target=candidate;
    if(target==null||target.hasLost()||!inner.canTarget(target))throw new IllegalStateException("Illegal partner target player");
    inner.getTargets().add(target);if(!inner.isTargetNumberValid()){inner.resetTargets();throw new IllegalStateException("Partner target restrictions failed");}
    boundTriggerInnerAbilities.add(inner);
    String original=card.getId()+":"+integer(row.get("original_ability_id"));String previous=selectedAbilityBindings.putIfAbsent(original,source(wrapper));if(previous!=null&&!previous.equals(source(wrapper)))throw new IllegalStateException("Ambiguous trigger identity binding");
    long token=EngineEvidence.enter(hook,receiver,args);activeTriggerPayment=wrapper;triggerPayments=0;
    try{if(!forge.ai.ComputerUtil.playStack(wrapper,player,game)||triggerPayments!=1)throw new IllegalStateException("Actual partner stack/payment failed");}finally{activeTriggerPayment=null;}
    EngineEvidence.leave(token,null);consumed++;return null;
   }
   if(payment){
    if(Set.of("basic_land_mana","fixed_tap_mana","selected_tap_mana").contains(row.get("decision_type").getAsString())){
     SpellAbility ability=(SpellAbility)args[1];Player player=controller.getPlayer();var game=player.getGame();CostPartMana part=(CostPartMana)args[0];bindAbility(row,ability);
     if(!part.toString().equals(row.get("component").getAsString()))throw new IllegalStateException("Mana component diverged: actual "+part+" expected "+row.get("component"));
     if(args[2]!=null||args[3]!=null||!Boolean.FALSE.equals(args[4])||player.hasLost()||ability.getActivatingPlayer()!=player||!ability.isSpell()||!ability.getHostCard().isInZone(ZoneType.Stack)||!player.getManaPool().isEmpty()||!part.toString().equals(row.get("component").getAsString())||part.getAmountOfX()!=0||ability.getXManaCostPaid()!=null||ability.getMaxWaterbend()!=null||ability.usesTargeting()||!ability.getMapParams().isEmpty()||!ability.getPayingMana().isEmpty()||ability.getPayCosts()==null||!ability.getPayCosts().isOnlyManaCost()||!String.valueOf(ability.getApi()).equals(row.get("ability_api").getAsString()))throw new IllegalStateException("Unsupported tap-mana payment context");
     if(ability.getHostCard().isCommander()&&(!row.has("commander")||!row.get("commander").getAsBoolean()||player.getCommanderCast(ability.getHostCard())!=integer(row.get("prior_commander_casts"))||integer(row.get("commander_tax"))!=2L*player.getCommanderCast(ability.getHostCard())||ability.getMayPlay()==null||!ability.getMayPlay().getHostCard().getName().equals("Commander Effect")))throw new IllegalStateException("Commander payment provenance diverged");
     ManaCostBeingPaid adjusted=new ManaCostBeingPaid(part.getManaCostFor(ability));CostAdjustment.adjust(adjusted,ability,player,null,false,false);
     if(row.has("adjusted_cost")&&!row.get("adjusted_cost").isJsonNull()){JsonObject cost=row.getAsJsonObject("adjusted_cost");JsonArray shards=new JsonArray();adjusted.getUnpaidShards().forEach(s->shards.add(s.toString()));if(!adjusted.toString().equals(cost.get("cost").getAsString())||adjusted.getGenericManaAmount()!=integer(cost.get("generic"))||!shards.equals(cost.get("unpaid_shards")))throw new IllegalStateException("Adjusted cost/tax differs from recorded payment choices");}
     ManaCostBeingPaid preview=new ManaCostBeingPaid(adjusted);Map<Integer,SpellAbility> sources=new LinkedHashMap<>();Map<Integer,Integer> remaining=new LinkedHashMap<>();Map<Integer,String> productionColors=new LinkedHashMap<>();
     for(JsonElement item:row.getAsJsonArray("operations")){
      JsonObject step=item.getAsJsonObject();String operation=step.get("op").getAsString();
      if(operation.equals("activate_basic")){
       int id=Math.toIntExact(integer(step.get("card_id")));Card card=null;for(Card candidate:player.getCardsIn(ZoneType.Battlefield))if(candidate.getId()==id)card=candidate;
       if(card==null||!(card.getType().isBasicLand()||Set.of("Sol Ring","Command Tower","Brushland").contains(card.getName()))||card.isCreature()||card.isTapped()||card.isPhasedOut()||card.getController()!=player||!card.getName().equals(step.get("card_name").getAsString())||sources.containsKey(id))throw new IllegalStateException("Unavailable basic mana source");
       SpellAbility chosen=null;for(SpellAbility candidate:card.getManaAbilities()){JsonObject params=new JsonObject();candidate.getMapParams().forEach(params::addProperty);if(params.equals(step.get("parameters"))){if(chosen!=null)throw new IllegalStateException("Ambiguous basic mana ability");chosen=candidate;}}
       if(chosen==null||!chosen.isManaAbility()||chosen.getPayCosts()==null||chosen.getPayCosts().getCostParts().size()!=1||!(chosen.getPayCosts().getCostParts().get(0) instanceof CostTap))throw new IllegalStateException("Unsupported basic mana activation");
       if(chosen.getSubAbility()!=null){SpellAbility sub=chosen.getSubAbility();if(!card.getName().equals("Brushland")||!String.valueOf(sub.getApi()).equals("DealDamage")||sub.getSubAbility()!=null||sub.usesTargeting()||!sub.getMapParams().equals(Map.of("DB","DealDamage","NumDmg","1","Defined","You")))throw new IllegalStateException("Unsupported mana subability");}
       if(!Set.of("W","U","B","R","G","C").contains(produced(chosen,step)))throw new IllegalStateException("Unsupported production color");
       chosen.setActivatingPlayer(player);if(step.has("color_choice")){String spec=chosen.getParam("Produced");if(!(card.getName().equals("Command Tower")&&spec.equals("Combo ColorIdentity")||card.getName().equals("Brushland")&&spec.equals("Combo G W"))||!chosen.getManaPart().canProduce(produced(chosen,step),chosen))throw new IllegalStateException("Illegal selected production color");}
       String amount=chosen.getParamOrDefault("Amount","1");if(!Set.of("1","2").contains(amount))throw new IllegalStateException("Unsupported mana production amount");
       chosen.setActivatingPlayer(player);if(!chosen.canPlay()||!chosen.getPayCosts().canPay(chosen,player,false))throw new IllegalStateException("Illegal basic mana activation");sources.put(id,chosen);remaining.put(id,Integer.parseInt(amount));productionColors.put(id,produced(chosen,step));
      }else if(operation.equals("spend")){
       JsonObject mana=step.getAsJsonObject("mana");int id=Math.toIntExact(integer(mana.get("source_card_id")));SpellAbility source=sources.get(id);
       if(source==null||remaining.getOrDefault(id,0)<=0||mana.get("snow").getAsBoolean()||mana.get("restricted").getAsBoolean()||!Objects.equals(productionColors.get(id),mana.get("color").getAsString()))throw new IllegalStateException("Illegal selected basic mana unit");
       Mana predicted=new Mana(MagicColor.fromName(mana.get("color").getAsString()),source.getHostCard(),source.getManaPart(),player);
       boolean expected=!step.has("expected_success")||step.get("expected_success").getAsBoolean();if(preview.isNeeded(predicted,player.getManaPool())!=expected)throw new IllegalStateException("Recorded mana attempt legality diverged");if(expected){if(!preview.payMana(predicted,player.getManaPool()))throw new IllegalStateException("Selected mana cannot pay adjusted cost");remaining.put(id,remaining.get(id)-1);}
      }else throw new IllegalStateException("Unsupported payment operation");
     }
     if(!preview.isPaid())throw new IllegalStateException("Incomplete recorded basic mana payment");
     long token=EngineEvidence.enter(hook,receiver,args);
     for(JsonElement item:row.getAsJsonArray("operations")){
      JsonObject step=item.getAsJsonObject();
      if(step.get("op").getAsString().equals("activate_basic")){
       SpellAbility source=sources.get(Math.toIntExact(integer(step.get("card_id"))));CostTap tap=source.getPayCosts().getCostPartByType(CostTap.class);
       if(!tap.canPay(source,player,false)||!tap.payAsDecided(player,PaymentDecision.number(0),source,false))throw new IllegalStateException("Basic mana tap payment failed");
       if(step.has("color_choice")){activeManaColor=step.getAsJsonObject("color_choice");activeManaAbility=source;source.getManaPart().setExpressChoice(activeManaColor.get("selected_color").getAsString());}
       try{game.getStack().add(source);if(activeManaColor!=null)throw new IllegalStateException("Recorded mana color choice not requested");}finally{activeManaColor=null;activeManaAbility=null;source.getManaPart().clearExpressChoice();}ability.getPayingManaAbilities().add(source);
      }else{
       JsonObject expected=step.getAsJsonObject("mana");Mana selected=null;for(Mana mana:player.getManaPool())if(mana.getSourceCard().getId()==integer(expected.get("source_card_id"))&&MagicColor.toShortString(mana.getColor()).equals(expected.get("color").getAsString())&&!mana.isSnow()&&!mana.isRestricted()){selected=mana;break;}
       if(selected==null)throw new IllegalStateException("Actual selected mana is unavailable");boolean expectedSuccess=!step.has("expected_success")||step.get("expected_success").getAsBoolean();boolean actualSuccess=player.getManaPool().tryPayCostWithMana(ability,adjusted,selected,false);if(actualSuccess!=expectedSuccess)throw new IllegalStateException("Actual selected mana payment result diverged");if(actualSuccess)ability.getPayingMana().add(selected);
      }
     }
     Map<Integer,Integer> observed=new LinkedHashMap<>();for(Mana mana:player.getManaPool()){int id=mana.getSourceCard().getId();if(!sources.containsKey(id)||mana.isSnow()||mana.isRestricted()||!Objects.equals(productionColors.get(id),MagicColor.toShortString(mana.getColor())))throw new IllegalStateException("Unexpected remaining mana");observed.merge(id,1,Integer::sum);}
     remaining.entrySet().removeIf(entry->entry.getValue()==0);if(!adjusted.isPaid()||!remaining.equals(observed))throw new IllegalStateException("Actual payment or remaining pool diverged");
     EngineEvidence.leave(token,true);consumed++;return true;
    }
    if(!"zero_effect_mana".equals(row.get("decision_type").getAsString())||!"pay".equals(row.get("payment_choice").getAsString())||args.length!=5||args[2]!=null||args[3]!=null||!Boolean.TRUE.equals(args[4]))throw new IllegalStateException("Unsupported mana payment choice");
    SpellAbility ability=(SpellAbility)args[1];CostPartMana part=(CostPartMana)args[0];Player player=controller.getPlayer();bindAbility(row,ability);
    JsonObject params=new JsonObject();ability.getMapParams().forEach(params::addProperty);
    if(player.hasLost()||ability.getActivatingPlayer()!=player||!String.valueOf(ability.getApi()).equals(row.get("ability_api").getAsString())||!params.equals(row.get("ability_parameters")))throw new IllegalStateException("Payment actor/source/domain diverged");
    Cost cost=ability.getPayCosts();
    if(cost==null||!cost.isOnlyManaCost()||!cost.getTotalMana().isZero()||part.getAmountOfX()!=0||!part.getManaCostFor(ability).isZero()||ability.getXManaCostPaid()!=null||ability.getMaxWaterbend()!=null||ability.hasParam("Announce")||!ability.getPayingMana().isEmpty())throw new IllegalStateException("Unsupported nonzero or resource-changing payment");
    // Mirror the engine's actual mana adjustment, with no AI payment selection.
    // Effect costs bypass spell taxes; waterbend and all non-mana costs reject above.
    ManaCostBeingPaid adjusted=new ManaCostBeingPaid(part.getManaCostFor(ability));CostAdjustment.adjust(adjusted,ability,player,null,false,true);
    if(!adjusted.isPaid()||adjusted.getXcounter()!=0)throw new IllegalStateException("Adjusted mana cost is not zero");
    return complete(hook,receiver,args,true);
   }
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
    if(args.length==0&&Set.of("plain_hand_permanent_spell","command_permanent_spell").contains(row.get("decision_type").getAsString())){
     turnContext(row,controller);Player player=controller.getPlayer();var game=player.getGame();
     if(game.getPhaseHandler().getPlayerTurn()!=player||!game.getStack().isEmpty()||!Set.of("MAIN1","MAIN2").contains(String.valueOf(game.getPhaseHandler().getPhase())))throw new IllegalStateException("Unsupported permanent spell timing");
     boolean commander=row.get("decision_type").getAsString().equals("command_permanent_spell");Card card=null;for(Card candidate:player.getCardsIn(commander?ZoneType.Command:ZoneType.Hand))if(candidate.getId()==integer(row.get("source_card_id")))card=candidate;
     if(card==null||card.getOwner()!=player||!card.getName().equals(row.get("source_name").getAsString())||!card.getManaCost().toString().equals(row.get("mana_cost").getAsString())||card.getManaCost().countX()!=0||card.isFaceDown())throw new IllegalStateException("Illegal recorded spell source");
     if(commander&&(!card.isCommander()||!player.getCommanders().contains(card)||player.getCommanderCast(card)!=integer(row.get("prior_commander_casts"))||integer(row.get("commander_tax"))!=2L*player.getCommanderCast(card)))throw new IllegalStateException("Commander designation or cast count diverged");
     SpellAbility selected=null;
     for(SpellAbility candidate:card.getSpellAbilities()){
      if(!candidate.isSpell()||!String.valueOf(candidate.getApi()).equals(row.get("selected_api").getAsString())||!candidate.getMapParams().isEmpty())continue;
      if(selected!=null)throw new IllegalStateException("Ambiguous permanent spell identity");selected=candidate;
     }
     if(selected==null||selected.getSubAbility()!=null||selected.usesTargeting()||selected.getPayCosts()==null||!selected.getPayCosts().isOnlyManaCost()||!selected.getPayCosts().getTotalMana().equals(card.getManaCost()))throw new IllegalStateException("Unsupported permanent spell choices or costs");
     if(commander){
      forge.game.card.CardPlayOption permission=null;
      for(var option:card.mayPlay(player))if(option.getHost().getName().equals("Commander Effect")&&option.getHost().getController()==player&&option.getHost().isInZone(ZoneType.Command)&&option.getPayManaCost()==forge.game.card.CardPlayOption.PayManaCost.YES&&option.getAltManaCost()==null&&!option.isIgnoreManaCostColor()&&!option.isIgnoreManaCostType()&&!option.isWithFlash()&&"Command".equals(option.getAbility().getParam("AffectedZone"))&&"Card.IsCommander+YouOwn".equals(option.getAbility().getParam("Affected"))){if(permission!=null)throw new IllegalStateException("Ambiguous commander cast permission");permission=option;}
      if(permission==null)throw new IllegalStateException("Missing live commander cast permission");selected=selected.copy();selected.setMayPlay(permission);
     }
     selected.setActivatingPlayer(player);if(!selected.canPlay())throw new IllegalStateException("Illegal permanent spell restrictions");
     if(commander&&row.has("original_ability_id")){String original=card.getId()+":"+integer(row.get("original_ability_id"));String previous=selectedAbilityBindings.putIfAbsent(original,source(selected));if(previous!=null&&!previous.equals(source(selected)))throw new IllegalStateException("Recorded commander ability binding reused ambiguously");}
     // Only select the actual live spell. Normal casting and payment must still
     // execute; this return does not move the card or grant a legal cast result.
     return complete(hook,receiver,args,Collections.singletonList(selected));
    }
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
   if(randomInput!=null){String last=randomInput.readLine();JsonObject terminal=last==null?null:JsonParser.parseString(last).getAsJsonObject();if(terminal==null||!"engine_random_complete".equals(terminal.get("kind").getAsString())||integer(terminal.get("requests"))!=randomConsumed||randomInput.readLine()!=null||!HexFormat.of().formatHex(randomDigest.digest()).equals(randomHash))throw new IllegalStateException("Incomplete or altered engine RNG input");randomInput.close();randomInput=null;}
  }catch(Exception e){failed=true;throw e;}finally{input.close();input=null;}
 }
}
