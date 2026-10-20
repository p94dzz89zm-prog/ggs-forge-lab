package forge.ai.bridge;

import com.google.gson.*;
import forge.card.MagicColor;
import forge.game.*;
import forge.game.card.*;
import forge.game.cost.*;
import forge.game.mana.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.ZoneType;
import java.nio.file.*;
import java.util.*;
import java.lang.reflect.RecordComponent;

/** Private omniscient referee tape. NEVER passed to a player or learner. */
public final class EngineEvidence {
 private static Game live;
 private static long next;
 private static java.io.BufferedReader reference;
 private static final List<JsonObject> pregameRandom=new ArrayList<>();
 private static final List<JsonObject> randomReference=new ArrayList<>();
 private static int referencePosition,randomPosition;
 public static synchronized void randomReset(long seed) {
  if(live!=null)throw new IllegalStateException("RNG reset in active game");
  pregameRandom.clear();randomReference.clear();reference=null;referencePosition=0;randomPosition=0;
  String file=System.getProperty("forge.referee.replayTape");
  if(file!=null)try {
   Path tape=Path.of(file);String expected=System.getProperty("forge.referee.replaySha256");
   java.security.MessageDigest hash=java.security.MessageDigest.getInstance("SHA-256");
   try(java.io.InputStream input=Files.newInputStream(tape)){byte[] buffer=new byte[65536];int n;while((n=input.read(buffer))!=-1)hash.update(buffer,0,n);}
   if(expected==null||!HexFormat.of().formatHex(hash.digest()).equals(expected))throw new IllegalStateException("Replay tape hash mismatch");
   try(java.io.BufferedReader input=Files.newBufferedReader(tape)) {
    String line;while((line=input.readLine())!=null) {
     JsonObject row=JsonParser.parseString(line).getAsJsonObject();
     if(row.get("kind").getAsString().equals("random_bits"))randomReference.add(row);
    }
   }
   reference=Files.newBufferedReader(tape);
  }catch(Exception e){throw new IllegalStateException("Cannot load verified replay tape",e);}
 }
 public static synchronized int randomBits(int bits,int generated) {
  int result=generated;
  if(reference!=null) {
   if(randomPosition>=randomReference.size())throw new IllegalStateException("Replay RNG exhausted");
   JsonObject expected=randomReference.get(randomPosition);
   if(expected.get("bits").getAsInt()!=bits)throw new IllegalStateException("Replay RNG request diverged");
   result=expected.get("value").getAsInt();
   if(bits<32&&(result<0||((long)result)>=(1L<<bits)))throw new IllegalStateException("Invalid replay random bits");
  }
  JsonObject row=new JsonObject();row.addProperty("kind","random_bits");row.addProperty("random_index",++randomPosition);row.addProperty("bits",bits);row.addProperty("value",result);
  if(live==null)pregameRandom.add(row);else write(row);return result;
 }
 private static final Map<Long,Call> calls=new LinkedHashMap<>();
 private static final Set<SpellAbility> describingAbilities=Collections.newSetFromMap(new IdentityHashMap<>());
 private static final ThreadLocal<Boolean> busy=ThreadLocal.withInitial(()->false);
 private record Call(String hook,Object receiver,Object[] args,boolean speculative){}
 private EngineEvidence(){}
 public static synchronized void begin(Game game) {
  if(!calls.isEmpty())throw new IllegalStateException("Unfinished engine evidence calls");
  live=game;next=0;for(JsonObject row:pregameRandom)write(row);pregameRandom.clear();
 }
 private static Player poolOwner(Object o) {if(live!=null)for(Player p:live.getRegisteredPlayers())if(p.getManaPool()==o)return p;return null;}
 private static Game gameOf(Object o) {
  if(o instanceof Game g)return g;
  if(live!=null&&(o==live.getAction()||o==live.getStack()))return live;
  if(o instanceof Player p)return p.getGame();
  if(o instanceof Card c)return c.getGame();
  if(o instanceof SpellAbility s)return s.getHostCard().getGame();
  if(o instanceof PlayerController c)return c.getPlayer().getGame();
  if(o instanceof CostPayment c)return gameOf(c.getAbility());
  if(o instanceof CostDecisionMakerBase c)return c.getPlayer().getGame();
  Player p=poolOwner(o);return p==null?null:p.getGame();
 }
 private static void write(JsonObject row) {
  String dir=System.getProperty("forge.audit.directory");if(dir==null)throw new IllegalStateException("Engine referee tape needs private audit directory");
  row.addProperty("format",1);row.addProperty("audience","offline_referee_only");
  row.addProperty("turn",live.getPhaseHandler().getTurn());
  if(live.getPhaseHandler().getPriorityPlayer()!=null)row.addProperty("priority_player_id",live.getPhaseHandler().getPriorityPlayer().getId());
  if(live.getPhaseHandler().getPlayerTurn()!=null)row.addProperty("turn_player_id",live.getPhaseHandler().getPlayerTurn().getId());row.addProperty("phase",String.valueOf(live.getPhaseHandler().getPhase()));
  ReplayCardIdentities.observe(row);
  if(reference!=null) {
   try {
    String line=reference.readLine();JsonObject expected=line==null?null:JsonParser.parseString(line).getAsJsonObject();
    if(expected!=null){expected.remove("evidence_game_id");expected.remove("stream_sequence");}
    if(expected==null||!equivalent(expected,row)) {
     JsonObject failure=new JsonObject();failure.addProperty("record_index",referencePosition);failure.add("expected",expected);failure.add("actual",row);
     DurableEvidence.atomic(Path.of(dir,"referee-divergence.json"),failure.toString());
     throw new IllegalStateException("Replay event divergence at "+referencePosition+" kind="+row.get("kind"));
    }
    referencePosition++;
   }catch(java.io.IOException e){throw new IllegalStateException("Replay read failed",e);}
  }
  try {DurableEvidence.append(Path.of(dir,"referee-events.jsonl"),row);}catch(Exception e){throw new IllegalStateException("Referee evidence failed",e);}
 }
 // Only this UI notification is derived from a Set<Card>. Its membership
 // matters; its iteration order is not a game choice or zone order.
 private static JsonElement normalizeNotifications(JsonElement value) {
  if(value.isJsonArray()){JsonArray a=new JsonArray();for(JsonElement e:value.getAsJsonArray())a.add(normalizeNotifications(e));return a;}
  if(!value.isJsonObject())return value;
  JsonObject o=new JsonObject();for(var e:value.getAsJsonObject().entrySet())o.add(e.getKey(),normalizeNotifications(e.getValue()));
  if(o.has("record_type")&&o.get("record_type").getAsString().equals("GameEventCardStatsChanged")&&o.has("cards")) {
   List<JsonElement> cards=new ArrayList<>();o.getAsJsonArray("cards").forEach(cards::add);cards.sort(Comparator.comparing(JsonElement::toString));JsonArray a=new JsonArray();cards.forEach(a::add);o.add("cards",a);
  }
  return o;
 }
 private static boolean equivalent(JsonObject expected,JsonObject actual) {
  return expected.equals(actual)||normalizeNotifications(expected).equals(normalizeNotifications(actual));
 }
 public static synchronized long enter(String hook,Object receiver,Object[] args) {
  if(live==null||busy.get())return 0;
  Game g=gameOf(receiver);if(g==null)for(Object a:args){g=gameOf(a);if(g!=null)break;}
  // Exclude cloned planning games; their speculative events are not live actions.
  if(g!=live)return 0;
  
  busy.set(true);
  try {
   boolean speculative=calls.values().stream().anyMatch(c->c.speculative);
   if((hook.startsWith("forge/ai/ComputerUtilMana.")||hook.startsWith("forge/game/mana/ManaPool.tryPayCostWithMana"))&&Boolean.TRUE.equals(args[3]))speculative=true;
   if(hook.startsWith("forge/game/cost/CostAdjustment.adjust(")&&args.length==6&&Boolean.TRUE.equals(args[4]))speculative=true;
   long parent=calls.isEmpty()?0:new ArrayList<>(calls.keySet()).get(calls.size()-1);
   long id=++next;calls.put(id,new Call(hook,receiver,args.clone(),speculative));JsonObject row=new JsonObject();row.addProperty("kind","engine_call");row.addProperty("call_id",id);row.addProperty("hook",hook);row.addProperty("parent_call_id",parent);row.addProperty("speculative",speculative);
   row.add("receiver",value(receiver,0));row.add("arguments",value(args,0));
   Player payer=receiver instanceof PlayerController c?c.getPlayer():poolOwner(receiver);
   for(Object a:args)if(a instanceof SpellAbility sa&&sa.getActivatingPlayer()!=null)payer=sa.getActivatingPlayer();
   if(receiver instanceof PlayerController pc && hook.contains(".playChosenSpellAbility(")){
    row.add("execution_state_before",initialState());row.add("execution_mana_before",value(pc.getPlayer().getManaPool(),0));
   }
   if(payer!=null && payer.getController() instanceof forge.ai.PlayerControllerAi
      && (hook.contains(".playChosenSpellAbility(") || hook.startsWith("forge/ai/ComputerUtilMana.payManaCost("))){
    JsonObject memory=new JsonObject();
    for(forge.ai.AiCardMemory.MemorySet set:forge.ai.AiCardMemory.MemorySet.values())
     memory.add(set.name(),value(forge.ai.AiCardMemory.getMemorySet(payer,set),0));
    row.add("actor_policy_memory",memory);
   }
   if(payer!=null){row.addProperty("actor_id",payer.getId());row.add("mana_context",manaContext(payer));}
   if(hook.startsWith("forge/game/GameAction.reveal(")) {
    JsonArray entitled=new JsonArray();for(Player p:live.getPlayers())entitled.add(p.getId());row.add("entitled_player_ids",entitled);row.addProperty("visibility_operation","reveal_all");
   }else if(hook.startsWith("forge/game/GameAction.revealTo(")){row.add("entitled_player_ids",ids((Iterable<?>)args[1]));row.addProperty("visibility_operation","look_specified");}
   else if(hook.contains(".reveal(")&&receiver instanceof PlayerController c){JsonArray entitled=new JsonArray();entitled.add(c.getPlayer().getId());row.add("entitled_player_ids",entitled);row.addProperty("visibility_operation","delivery");}
   if(hook.startsWith("forge/game/player/Player.announceManaPool(")){row.add("entitled_player_ids",ids(live.getPlayers()));row.addProperty("visibility_operation","public_mana_pool_announcement");row.addProperty("rules_basis","CR106.4a/106.4b/118.3a");JsonObject payload=new JsonObject();payload.add("counts",value(args[1],0));payload.addProperty("reason",(String)args[0]);payload.addProperty("player_id",((Player)receiver).getId());row.add("public_payload",payload);row.addProperty("visibility_scope","Only public_payload is disclosed; surrounding context is private referee evidence");}
   if(hook.startsWith("forge/game/Game.fireEvent")) {
    if(args[0] instanceof forge.game.event.GameEventGameStarted)row.add("initial_state",initialState());
    if(args[0] instanceof forge.game.event.GameEventCombatChanged)row.add("combat",value(live.getCombat(),0));
    if(args[0] instanceof forge.game.event.GameEventSpellAbilityCast cast) {
     SpellAbility announced=announcedAbility(cast.sa().getId());
     if(announced!=null)row.add("announced_ability",ability(announced));
     row.addProperty("announced_ability_available",announced!=null);
     JsonArray audience=new JsonArray();for(Player p:live.getPlayers())audience.add(p.getId());row.add("entitled_player_ids",audience);row.addProperty("visibility_operation","public_stack_announcement");
     row.addProperty("source_identity_disclosed",!cast.sa().getHostCard().isFaceDown());row.add("announced_source",value(cast.sa().getHostCard(),0));
     row.addProperty("visibility_duration_basis","CR601.2a/602.2a; hidden-zone ability source remains revealed until ability leaves stack");
    }
   }
   write(row);return id;
  }finally{busy.set(false);}
 }
 public static synchronized void leave(long id,Object result) {
  if(id==0)return;
  Player announcementPlayer=null;String announcementReason=null;
  busy.set(true);
  try {
   Call c=calls.remove(id);if(c==null)throw new IllegalStateException("Unpaired referee call");
   JsonObject row=new JsonObject();row.addProperty("kind","engine_return");row.addProperty("call_id",id);row.addProperty("hook",c.hook);row.add("result",value(result,0));row.add("arguments_after",value(c.args,0));
   if(c.receiver instanceof CostPayment p)row.add("ability_after",value(p.getAbility(),0));
   if(c.receiver instanceof PlayerController pc && c.hook.contains(".playChosenSpellAbility(")){
    row.add("execution_state_after",initialState());row.add("execution_mana_after",value(pc.getPlayer().getManaPool(),0));
   }
   if(c.hook.startsWith("forge/game/Game.onPlayerLost"))row.add("elimination_state_after",initialState());
   Player poolPlayer=poolOwner(c.receiver);if(poolPlayer!=null)row.add("mana_pool_after",value(poolPlayer.getManaPool(),0));
   write(row);
   if(c.receiver instanceof PlayerController controller&&!controller.getPlayer().getManaPool().isEmpty()){
    boolean paid=c.hook.endsWith(".payManaCost(Lforge/game/cost/CostPartMana;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Lforge/game/mana/ManaConversionMatrix;Z)Z")&&Boolean.TRUE.equals(result);
    boolean passed=c.hook.endsWith(".chooseSpellAbilityToPlay()Ljava/util/List;")&&(result==null||result instanceof Collection<?> collection&&collection.isEmpty())&&calls.values().stream().noneMatch(other->other.hook.endsWith(".chooseSpellAbilityToPlay()Ljava/util/List;"));
    if(paid||passed){announcementPlayer=controller.getPlayer();announcementReason=paid?"after_cost_payment":"priority_pass";}
   }
  }finally{busy.set(false);}
  if(announcementPlayer!=null){Map<String,Integer> counts=new TreeMap<>();for(Mana mana:announcementPlayer.getManaPool())counts.merge(MagicColor.toShortString(mana.getColor()),1,Integer::sum);long token=enter("forge/game/player/Player.announceManaPool(Ljava/lang/String;Ljava/util/Map;)V",announcementPlayer,new Object[]{announcementReason,counts});leave(token,null);}
 }
 public static synchronized void finish() {
  if(!calls.isEmpty())throw new IllegalStateException("Incomplete referee calls: "+calls.size());
  if(DecisionReplay.enabled())try{DecisionReplay.finish();ReplayCardIdentities.finish();}catch(Exception e){throw new IllegalStateException("Decision reconstruction incomplete; no terminal seal",e);}
  JsonObject row=new JsonObject();row.addProperty("kind","engine_tape_complete");row.addProperty("calls",next);row.addProperty("rules_approved",false);row.add("final_state",initialState());write(row);if(reference!=null)try {if(reference.readLine()!=null)throw new IllegalStateException("Unconsumed replay events");reference.close();}catch(java.io.IOException e){throw new IllegalStateException(e);}live=null;
 }
 private static JsonArray ids(Iterable<?> values){JsonArray a=new JsonArray();for(Object v:values)if(v instanceof Player p)a.add(p.getId());return a;}
 private static SpellAbility announcedAbility(int id) {
  for(SpellAbilityStackInstance instance:live.getStack())if(instance.getSpellAbility().getId()==id)return instance.getSpellAbility();
  for(Call call:calls.values())for(Object arg:call.args)if(arg instanceof SpellAbility s&&s.getId()==id)return s;
  return null;
 }
 private static JsonObject manaContext(Player p) {
  JsonObject o=new JsonObject();o.add("pool",value(p.getManaPool(),0));JsonArray sources=new JsonArray();
  for(Card c:p.getCardsIn(ZoneType.Battlefield,false))if(!c.getManaAbilities().isEmpty()) {
   JsonObject source=card(c);JsonArray abilities=new JsonArray();for(SpellAbility s:c.getManaAbilities())abilities.add(ability(s));source.add("mana_abilities",abilities);sources.add(source);
  }
  JsonObject conversions=new JsonObject();for(byte color:new byte[]{1,2,4,8,16,0})conversions.addProperty(MagicColor.toShortString(color),p.getManaPool().getPossibleColorUses(color));o.add("possible_color_uses",conversions);o.addProperty("snow_for_color",p.getManaPool().isSnowForColor());
  o.add("potential_sources",sources);o.addProperty("availability_basis","current battlefield mana abilities; not a claim all are legally activatable");return o;
 }
 private static JsonObject initialState() {
  JsonObject o=new JsonObject();o.addProperty("format",live.getRules().getGameType().toString());JsonArray players=new JsonArray();
  for(Player p:live.getRegisteredPlayers()) {
   JsonObject state=new JsonObject();state.addProperty("id",p.getId());state.addProperty("life",p.getLife());state.addProperty("active",live.getPlayers().contains(p));state.addProperty("lost",p.hasLost());state.addProperty("won",p.hasWon());state.addProperty("poison",p.getPoisonCounters());
   if(p.getOutcome()!=null){state.addProperty("loss_reason",String.valueOf(p.getOutcome().lossState));state.addProperty("loss_source",p.getOutcome().loseConditionSpell);state.addProperty("alternate_win_source",p.getOutcome().altWinSourceName);}
   JsonObject damage=new JsonObject(),casts=new JsonObject();for(var e:p.getCommanderDamage())damage.addProperty(String.valueOf(e.getKey().getId()),e.getValue());for(Card c:p.getCommanders())casts.addProperty(String.valueOf(c.getId()),p.getCommanderCast(c));state.add("commander_damage",damage);state.add("commander_casts",casts);
   for(ZoneType z:ZoneType.values()) {JsonArray cards=new JsonArray();for(Card c:p.getCardsIn(z,false))cards.add(card(c));state.add(z.name(),cards);}
   players.add(state);
  }
  o.add("players",players);o.addProperty("visibility","private ordered zones; never pilot input");return o;
 }
 private static JsonObject card(Card c) {
  JsonObject o=new JsonObject();o.addProperty("card_id",c.getId());o.addProperty("name",c.getName());o.addProperty("owner_id",c.getOwner().getId());o.addProperty("controller_id",c.getZone()!=null&&(c.getZone().getZoneType()==ZoneType.Battlefield||c.getZone().getZoneType()==ZoneType.Stack)?c.getController().getId():c.getOwner().getId());o.addProperty("controller_basis",c.getZone()!=null&&(c.getZone().getZoneType()==ZoneType.Battlefield||c.getZone().getZoneType()==ZoneType.Stack)?"engine":"owner fallback outside battlefield/stack; CR108.4");o.addProperty("zone",c.getZone()==null?null:c.getZone().getZoneType().name());o.addProperty("face_down",c.isFaceDown());o.addProperty("tapped",c.isTapped());o.addProperty("phased_out",c.isPhasedOut());o.addProperty("commander",c.isCommander());o.addProperty("mana_cost",c.getManaCost().toString());
  o.addProperty("private_original_name",c.getState(forge.card.CardStateName.Original).getName());
  SpellAbility cast=c.getCastSA();o.addProperty("cast_ability_id",cast==null?null:cast.getId());o.addProperty("cast_chosen_x",cast==null?null:cast.getXManaCostPaid());
  o.addProperty("cast_x_basis","card cast-SA history; null means unavailable, not zero; current announced X is on the spell ability");
  o.addProperty("marked_damage",c.getDamage());JsonObject counters=new JsonObject();for(var e:c.getCounters().entrySet())counters.addProperty(e.getElement().getName(),e.getCount());o.add("counters",counters);
  JsonArray viewers=new JsonArray();for(Player p:live.getPlayers())if(c.isFaceDown()?c.getView().canFaceDownBeShownTo(p.getView()):c.getView().canBeShownTo(p.getView()))viewers.add(p.getId());o.add("engine_identity_visible_to",viewers);o.addProperty("visibility_basis","engine permission at this event; temporary reveal entitlement is separately recorded");return o;
 }
 private static JsonObject ability(SpellAbility s) {
  if(!describingAbilities.add(s)){JsonObject ref=new JsonObject();ref.addProperty("ability_ref",s.getId());ref.addProperty("source_card_id",s.getHostCard().getId());return ref;}
  try{return describeAbility(s);}finally{describingAbilities.remove(s);}
 }
 private static JsonObject describeAbility(SpellAbility s) {
  JsonObject o=new JsonObject();o.addProperty("ability_id",s.getId());o.add("source",card(s.getHostCard()));if(s.getActivatingPlayer()!=null)o.addProperty("activating_player_id",s.getActivatingPlayer().getId());o.addProperty("api",String.valueOf(s.getApi()));o.add("parameters",value(s.getMapParams(),1));
  if(s.getHostCard().getName().equals("Misty Rainforest")&&s.getOriginalAbility()!=null){SpellAbility original=s.getOriginalAbility();o.addProperty("native_original_ability_id",original.getId());o.addProperty("native_original_source_card_id",original.getHostCard().getId());o.addProperty("native_original_distinct_instance",original!=s);}
  String description=s.getDescription();Integer chosen=s.getXManaCostPaid();
  o.addProperty("engine_description",description);
  o.addProperty("description",chosen==null?description:description.replaceAll("\\(X=[0-9]+\\)","(X="+chosen+")"));
  o.addProperty("pay_costs",String.valueOf(s.getPayCosts()));o.addProperty("spell",s.isSpell());o.addProperty("activated",s.isActivatedAbility());o.addProperty("trigger",s.isTrigger());o.addProperty("x",chosen);o.addProperty("chosen_x",chosen);o.addProperty("chosen_x_basis","SpellAbility.getXManaCostPaid; never infer from cached description or card cast history");
  if(s.getManaPart()!=null){o.addProperty("mana_produced_spec",s.getManaPart().getOrigProduced());o.addProperty("mana_restrictions",s.getManaPart().getManaRestrictions());o.addProperty("mana_extra_restrictions",s.getManaPart().getExtraManaRestriction());}
  JsonArray alts=new JsonArray();for(AlternativeCost a:AlternativeCost.values())if(s.isAlternativeCost(a))alts.add(a.name());o.add("alternative_costs",alts);JsonArray opts=new JsonArray();for(OptionalCost a:s.getOptionalCosts())opts.add(a.name());o.add("optional_costs",opts);o.add("targets",value(s.getUniqueTargets(),1));o.add("paying_mana",value(s.getPayingMana(),1));
  o.add("direct_targets",value(s.getTargets(),1));o.addProperty("legacy_targets_basis","SpellAbility.getUniqueTargets traverses parents; direct_targets records this ability");
  if(!s.getOptionalKeywords().isEmpty()){
   JsonArray payments=new JsonArray();
   for(forge.game.keyword.Keyword type:s.getOptionalKeywords())for(forge.game.keyword.KeywordInterface k:s.getHostCard().getKeywords(type)){
    JsonObject payment=new JsonObject();payment.add("keyword",value(k,1));
    payment.addProperty("amount",s.getOptionalKeywordAmount(k));payments.add(payment);
   }
   o.add("optional_keyword_payments",payments);
  }
  if(s.getReplacementEffect()!=null){o.add("replacement_effect",value(s.getReplacementEffect(),1));o.addProperty("replacement_overriding_instance_equal",s.getReplacementEffect().getOverridingAbility()==s);o.add("replacement_affected",value(s.getReplacingObject(forge.game.ability.AbilityKey.Card),1));}
  JsonObject replacementBinding=DecisionReplay.replacementSourceEvidence(s);if(replacementBinding!=null)o.add("causal_replacement_binding",replacementBinding);
  if(s instanceof forge.game.trigger.WrappedAbility wrapper){o.addProperty("wrapper",true);o.add("wrapped_ability",ability(wrapper.getWrappedAbility()));}
  if(s.getHostCard().getName().equals("Cultivate")&&s.getSubAbility()!=null)o.add("sub_ability",ability(s.getSubAbility()));
  if(s.getHostCard().isCommander()&&s.getActivatingPlayer()!=null)o.addProperty("prior_commander_casts",s.getActivatingPlayer().getCommanderCast(s.getHostCard()));return o;
 }
 private static JsonElement value(Object v,int depth) {
  if(v==null)return JsonNull.INSTANCE;
  if(v instanceof JsonElement j)return j;
  if(v instanceof Number n)return new JsonPrimitive(n);
  if(v instanceof Boolean b)return new JsonPrimitive(b);
  if(v instanceof String||v instanceof Enum<?>)return new JsonPrimitive(v.toString());
  // A player view is a finite identity leaf. Preserve it even when the enclosing
  // blocker multimap reaches the recursion limit; do not expand player graphs.
  if(v instanceof PlayerView p){JsonObject o=new JsonObject();o.addProperty("view_id",p.getId());o.addProperty("name",p.getName());return o;}
  if(depth>7){JsonObject o=new JsonObject();o.addProperty("unencoded",v.getClass().getName());o.addProperty("reason","depth");return o;}
  if(v instanceof Card c)return card(c);
  if(v instanceof forge.game.keyword.KeywordInterface k){
   JsonObject o=new JsonObject();o.addProperty("keyword_type",v.getClass().getName());
   o.addProperty("keyword",k.getKeyword().name());o.addProperty("original",k.getOriginal());
   o.add("source",value(k.getHostCard(),depth+1));o.addProperty("intrinsic",k.isIntrinsic());
   if(k instanceof forge.game.keyword.KeywordWithCostInterface c){
    o.addProperty("cost_string",c.getCostString());o.addProperty("cost_text",c.getCost().toString());
    o.add("mana_cost",c.getCost().getCostMana()==null?JsonNull.INSTANCE:value(new ManaCostBeingPaid(c.getCost().getCostMana().getMana()),depth+1));
   }
   return o;
  }
  if(v instanceof Player p){JsonObject o=new JsonObject();o.addProperty("player_id",p.getId());o.addProperty("life",p.getLife());o.addProperty("lost",p.hasLost());return o;}
  if(v instanceof PlayerController c)return value(c.getPlayer(),depth+1);
  if(v instanceof SpellAbility s)return ability(s);
  if(v instanceof Mana m){JsonObject o=new JsonObject();o.addProperty("color",MagicColor.toShortString(m.getColor()));o.addProperty("source_card_id",m.getSourceCard().getId());o.addProperty("snow",m.isSnow());o.addProperty("restricted",m.isRestricted());if(m.getManaAbility()!=null)o.addProperty("restrictions",m.getManaAbility().getManaRestrictions()+";"+m.getManaAbility().getExtraManaRestriction());return o;}
  if(v instanceof SpellAbilityStackInstance s){JsonObject o=new JsonObject();o.addProperty("stack_instance_id",s.getId());o.add("ability",ability(s.getSpellAbility()));o.add("targets",value(s.getTargetChoices(),depth+1));o.add("activating_player",value(s.getActivatingPlayer(),depth+1));return o;}
  if(v instanceof SpellAbilityView s){JsonObject o=new JsonObject();o.addProperty("ability_id",s.getId());o.add("source",value(s.getHostCard(),depth+1));o.addProperty("description",s.getDescription());o.addProperty("spell",s.isSpell());return o;}
  if(v instanceof StackItemView s){JsonObject o=new JsonObject();o.addProperty("stack_instance_id",s.getId());o.add("source",value(s.getSourceCard(),depth+1));o.add("activating_player",value(s.getActivatingPlayer(),depth+1));o.add("target_cards",value(s.getTargetCards(),depth+1));o.add("target_players",value(s.getTargetPlayers(),depth+1));o.addProperty("text",s.getText());return o;}
  if(v instanceof DelayedReveal d){JsonObject o=new JsonObject();o.add("cards",value(d.getCards(),depth+1));o.add("zones",value(d.getZone(),depth+1));o.add("owner",value(d.getOwner(),depth+1));o.addProperty("message",d.getMessagePrefix());return o;}
  if(v instanceof forge.game.combat.Combat combat){JsonObject o=new JsonObject();o.add("attacking_player",value(combat.getAttackingPlayer(),depth+1));JsonArray attacks=new JsonArray();for(Card c:combat.getAttackers()){JsonObject attack=new JsonObject();attack.add("attacker",card(c));attack.add("defender",value(combat.getDefenderByAttacker(c),depth+1));attack.add("blockers",value(combat.getBlockers(c),depth+1));attack.addProperty("blocked",combat.isBlocked(c));attacks.add(attack);}o.add("attacks",attacks);return o;}
  if(v instanceof org.apache.commons.lang3.tuple.Pair<?,?> pair){JsonObject o=new JsonObject();o.add("left",value(pair.getLeft(),depth+1));o.add("right",value(pair.getRight(),depth+1));return o;}
  if(v instanceof com.google.common.collect.Multimap<?,?> map)return value(map.asMap(),depth+1);
  if(v instanceof CardTraitBase t){JsonObject o=new JsonObject();o.addProperty("trait_type",v.getClass().getName());o.add("source",card(t.getHostCard()));o.add("parameters",value(t.getMapParams(),depth+1));return o;}
  if(v instanceof CostDecisionMakerBase d){JsonObject o=new JsonObject();o.addProperty("decision_maker_type",v.getClass().getName());o.add("player",value(d.getPlayer(),depth+1));o.addProperty("effect",d.isEffect());o.addProperty("pays_right_after_decision",d.paysRightAfterDecision());return o;}
  if(v instanceof forge.game.ability.SpellAbilityEffect){JsonObject o=new JsonObject();o.addProperty("effect_implementation",v.getClass().getName());return o;}
  if(v instanceof Game||v instanceof GameAction){JsonObject o=new JsonObject();o.addProperty("context_type",v.getClass().getName());return o;}
  if(v instanceof CardView c){JsonObject o=new JsonObject();o.addProperty("view_id",c.getId());o.addProperty("name",c.getName());o.add("owner",value(c.getOwner(),depth+1));o.add("controller",value(c.getController(),depth+1));o.addProperty("zone",String.valueOf(c.getZone()));o.addProperty("face_down",c.isFaceDown());o.addProperty("power",c.getCurrentState().getPower());o.addProperty("toughness",c.getCurrentState().getToughness());return o;}
  if(v instanceof ManaCostBeingPaid cost){JsonObject o=new JsonObject();o.addProperty("cost",cost.toString());o.addProperty("generic",cost.getGenericManaAmount());o.addProperty("remaining_mana_value",cost.getConvertedManaCost());o.add("unpaid_shards",value(cost.getUnpaidShards(),depth+1));return o;}
  if(v instanceof CostPayment p){JsonObject o=new JsonObject();o.addProperty("base_cost",p.getCost().toString());o.add("ability",ability(p.getAbility()));return o;}
  if(v instanceof PaymentDecision p){JsonObject o=new JsonObject();o.addProperty("count",p.c);o.addProperty("type",p.type);o.add("cards",value(p.cards,depth+1));o.add("mana",value(p.mana,depth+1));o.add("players",value(p.players,depth+1));o.add("abilities",value(p.sp,depth+1));return o;}
  if(v instanceof CostPartWithList p){JsonObject o=new JsonObject();o.addProperty("cost",p.toString());o.add("paid_cards",value(p.getCardList(),depth+1));o.add("lki_cards",value(p.getLKIList(),depth+1));return o;}
  if(v instanceof Cost||v instanceof CostPart)return new JsonPrimitive(v.toString());
  if(v instanceof Map<?,?> m){
   if(m.keySet().stream().allMatch(k->k instanceof String||k instanceof Enum<?>||k instanceof Number)){JsonObject o=new JsonObject();for(var e:m.entrySet())o.add(String.valueOf(e.getKey()),value(e.getValue(),depth+1));return o;}
   JsonArray entries=new JsonArray();for(var e:m.entrySet()){JsonObject pair=new JsonObject();pair.add("key",value(e.getKey(),depth+1));pair.add("value",value(e.getValue(),depth+1));entries.add(pair);}JsonObject o=new JsonObject();o.add("map_entries",entries);return o;
  }
  if(v instanceof Iterable<?> it){JsonArray a=new JsonArray();for(Object x:it)a.add(value(x,depth+1));return a;}
  if(v instanceof Object[] array)return value(Arrays.asList(array),depth+1);
  if(v.getClass().isRecord()) {JsonObject o=new JsonObject();o.addProperty("record_type",v.getClass().getSimpleName());try{for(RecordComponent c:v.getClass().getRecordComponents())o.add(c.getName(),value(c.getAccessor().invoke(v),depth+1));}catch(Exception e){throw new IllegalStateException(e);}return o;}
  if(v instanceof forge.game.GameEntityView e){JsonObject o=new JsonObject();o.addProperty("view_id",e.getId());o.addProperty("name",e.getName());return o;}
  JsonObject o=new JsonObject();o.addProperty("unencoded",v.getClass().getName());return o;
 }
}
