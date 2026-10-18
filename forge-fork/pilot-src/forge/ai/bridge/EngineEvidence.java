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
 private static final ThreadLocal<Boolean> busy=ThreadLocal.withInitial(()->false);
 private record Call(String hook,Object receiver,Object[] args){}
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
  row.addProperty("turn",live.getPhaseHandler().getTurn());row.addProperty("phase",String.valueOf(live.getPhaseHandler().getPhase()));
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
  try {DurableEvidence.append(Path.of(dir,"referee-events.jsonl"),row.toString());}catch(Exception e){throw new IllegalStateException("Referee evidence failed",e);}
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
   boolean speculative=calls.values().stream().anyMatch(c->c.hook.startsWith("forge/ai/ComputerUtilMana.")&&Boolean.TRUE.equals(c.args[3]));
   if((hook.startsWith("forge/ai/ComputerUtilMana.")||hook.startsWith("forge/game/mana/ManaPool.tryPayCostWithMana"))&&Boolean.TRUE.equals(args[3]))speculative=true;
   long parent=calls.isEmpty()?0:new ArrayList<>(calls.keySet()).get(calls.size()-1);
   long id=++next;calls.put(id,new Call(hook,receiver,args.clone()));JsonObject row=new JsonObject();row.addProperty("kind","engine_call");row.addProperty("call_id",id);row.addProperty("hook",hook);row.addProperty("parent_call_id",parent);row.addProperty("speculative",speculative);
   row.add("receiver",value(receiver,0));row.add("arguments",value(args,0));
   Player payer=receiver instanceof PlayerController c?c.getPlayer():poolOwner(receiver);
   for(Object a:args)if(a instanceof SpellAbility sa&&sa.getActivatingPlayer()!=null)payer=sa.getActivatingPlayer();
   if(payer!=null){row.addProperty("actor_id",payer.getId());row.add("mana_context",manaContext(payer));}
   if(hook.startsWith("forge/game/GameAction.reveal(")) {
    JsonArray entitled=new JsonArray();for(Player p:live.getPlayers())entitled.add(p.getId());row.add("entitled_player_ids",entitled);row.addProperty("visibility_operation","reveal_all");
   }else if(hook.startsWith("forge/game/GameAction.revealTo(")){row.add("entitled_player_ids",ids((Iterable<?>)args[1]));row.addProperty("visibility_operation","look_specified");}
   else if(hook.contains(".reveal(")&&receiver instanceof PlayerController c){JsonArray entitled=new JsonArray();entitled.add(c.getPlayer().getId());row.add("entitled_player_ids",entitled);row.addProperty("visibility_operation","delivery");}
   if(hook.startsWith("forge/game/Game.fireEvent")&&args[0].getClass().getSimpleName().equals("GameEventGameStarted"))row.add("initial_state",initialState());
   write(row);return id;
  }finally{busy.set(false);}
 }
 public static synchronized void leave(long id,Object result) {
  if(id==0)return;
  busy.set(true);
  try {
   Call c=calls.remove(id);if(c==null)throw new IllegalStateException("Unpaired referee call");
   JsonObject row=new JsonObject();row.addProperty("kind","engine_return");row.addProperty("call_id",id);row.addProperty("hook",c.hook);row.add("result",value(result,0));row.add("arguments_after",value(c.args,0));
   if(c.receiver instanceof CostPayment p)row.add("ability_after",value(p.getAbility(),0));
   write(row);
  }finally{busy.set(false);}
 }
 public static synchronized void finish() {
  if(!calls.isEmpty())throw new IllegalStateException("Incomplete referee calls: "+calls.size());
  JsonObject row=new JsonObject();row.addProperty("kind","engine_tape_complete");row.addProperty("calls",next);row.addProperty("rules_approved",false);write(row);if(reference!=null)try {if(reference.readLine()!=null)throw new IllegalStateException("Unconsumed replay events");reference.close();}catch(java.io.IOException e){throw new IllegalStateException(e);}live=null;
 }
 private static JsonArray ids(Iterable<?> values){JsonArray a=new JsonArray();for(Object v:values)if(v instanceof Player p)a.add(p.getId());return a;}
 private static JsonObject manaContext(Player p) {
  JsonObject o=new JsonObject();o.add("pool",value(p.getManaPool(),0));JsonArray sources=new JsonArray();
  for(Card c:p.getCardsIn(ZoneType.Battlefield,false))if(!c.getManaAbilities().isEmpty()) {
   JsonObject source=card(c);JsonArray abilities=new JsonArray();for(SpellAbility s:c.getManaAbilities())abilities.add(ability(s));source.add("mana_abilities",abilities);sources.add(source);
  }
  o.add("potential_sources",sources);o.addProperty("availability_basis","current battlefield mana abilities; not a claim all are legally activatable");return o;
 }
 private static JsonObject initialState() {
  JsonObject o=new JsonObject();o.addProperty("format",live.getRules().getGameType().toString());JsonArray players=new JsonArray();
  for(Player p:live.getRegisteredPlayers()) {
   JsonObject state=new JsonObject();state.addProperty("id",p.getId());state.addProperty("life",p.getLife());
   for(ZoneType z:ZoneType.values()) {JsonArray cards=new JsonArray();for(Card c:p.getCardsIn(z,false))cards.add(card(c));state.add(z.name(),cards);}
   players.add(state);
  }
  o.add("players",players);o.addProperty("visibility","private ordered zones; never pilot input");return o;
 }
 private static JsonObject card(Card c) {
  JsonObject o=new JsonObject();o.addProperty("card_id",c.getId());o.addProperty("name",c.getName());o.addProperty("owner_id",c.getOwner().getId());o.addProperty("controller_id",c.getController().getId());o.addProperty("zone",c.getZone()==null?null:c.getZone().getZoneType().name());o.addProperty("face_down",c.isFaceDown());o.addProperty("tapped",c.isTapped());o.addProperty("phased_out",c.isPhasedOut());o.addProperty("commander",c.isCommander());o.addProperty("mana_cost",c.getManaCost().toString());return o;
 }
 private static JsonObject ability(SpellAbility s) {
  JsonObject o=new JsonObject();o.addProperty("ability_id",s.getId());o.add("source",card(s.getHostCard()));if(s.getActivatingPlayer()!=null)o.addProperty("activating_player_id",s.getActivatingPlayer().getId());o.addProperty("api",String.valueOf(s.getApi()));o.addProperty("description",s.getDescription());o.addProperty("pay_costs",String.valueOf(s.getPayCosts()));o.addProperty("spell",s.isSpell());o.addProperty("activated",s.isActivatedAbility());o.addProperty("trigger",s.isTrigger());o.addProperty("x",s.getXManaCostPaid());
  if(s.getManaPart()!=null){o.addProperty("mana_produced_spec",s.getManaPart().getOrigProduced());o.addProperty("mana_restrictions",s.getManaPart().getManaRestrictions());o.addProperty("mana_extra_restrictions",s.getManaPart().getExtraManaRestriction());}
  JsonArray alts=new JsonArray();for(AlternativeCost a:AlternativeCost.values())if(s.isAlternativeCost(a))alts.add(a.name());o.add("alternative_costs",alts);JsonArray opts=new JsonArray();for(OptionalCost a:s.getOptionalCosts())opts.add(a.name());o.add("optional_costs",opts);o.add("targets",value(s.getUniqueTargets(),1));o.add("paying_mana",value(s.getPayingMana(),1));
  if(s.getHostCard().isCommander()&&s.getActivatingPlayer()!=null)o.addProperty("prior_commander_casts",s.getActivatingPlayer().getCommanderCast(s.getHostCard()));return o;
 }
 private static JsonElement value(Object v,int depth) {
  if(v==null)return JsonNull.INSTANCE;
  if(v instanceof JsonElement j)return j;
  if(v instanceof Number n)return new JsonPrimitive(n);
  if(v instanceof Boolean b)return new JsonPrimitive(b);
  if(v instanceof String||v instanceof Enum<?>)return new JsonPrimitive(v.toString());
  if(depth>7){JsonObject o=new JsonObject();o.addProperty("unencoded",v.getClass().getName());o.addProperty("reason","depth");return o;}
  if(v instanceof Card c)return card(c);
  if(v instanceof Player p){JsonObject o=new JsonObject();o.addProperty("player_id",p.getId());o.addProperty("life",p.getLife());o.addProperty("lost",p.hasLost());return o;}
  if(v instanceof PlayerController c)return value(c.getPlayer(),depth+1);
  if(v instanceof SpellAbility s)return ability(s);
  if(v instanceof Mana m){JsonObject o=new JsonObject();o.addProperty("color",MagicColor.toShortString(m.getColor()));o.addProperty("source_card_id",m.getSourceCard().getId());o.addProperty("snow",m.isSnow());o.addProperty("restricted",m.isRestricted());if(m.getManaAbility()!=null)o.addProperty("restrictions",m.getManaAbility().getManaRestrictions()+";"+m.getManaAbility().getExtraManaRestriction());return o;}
  if(v instanceof CostPayment p){JsonObject o=new JsonObject();o.addProperty("base_cost",p.getCost().toString());o.add("ability",ability(p.getAbility()));return o;}
  if(v instanceof PaymentDecision p){JsonObject o=new JsonObject();o.addProperty("count",p.c);o.addProperty("type",p.type);o.add("cards",value(p.cards,depth+1));o.add("mana",value(p.mana,depth+1));o.add("players",value(p.players,depth+1));o.add("abilities",value(p.sp,depth+1));return o;}
  if(v instanceof CostPartWithList p){JsonObject o=new JsonObject();o.addProperty("cost",p.toString());o.add("paid_cards",value(p.getCardList(),depth+1));o.add("lki_cards",value(p.getLKIList(),depth+1));return o;}
  if(v instanceof Cost||v instanceof CostPart||v instanceof ManaCostBeingPaid)return new JsonPrimitive(v.toString());
  if(v instanceof Map<?,?> m){JsonObject o=new JsonObject();for(var e:m.entrySet())o.add(String.valueOf(e.getKey()),value(e.getValue(),depth+1));return o;}
  if(v instanceof Iterable<?> it){JsonArray a=new JsonArray();for(Object x:it)a.add(value(x,depth+1));return a;}
  if(v instanceof Object[] array)return value(Arrays.asList(array),depth+1);
  if(v.getClass().isRecord()) {JsonObject o=new JsonObject();o.addProperty("record_type",v.getClass().getSimpleName());try{for(RecordComponent c:v.getClass().getRecordComponents())o.add(c.getName(),value(c.getAccessor().invoke(v),depth+1));}catch(Exception e){throw new IllegalStateException(e);}return o;}
  if(v instanceof forge.game.GameEntityView e){JsonObject o=new JsonObject();o.addProperty("view_id",e.getId());o.addProperty("name",e.getName());return o;}
  JsonObject o=new JsonObject();o.addProperty("unencoded",v.getClass().getName());return o;
 }
}
