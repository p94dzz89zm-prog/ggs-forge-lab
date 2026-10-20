package forge.ai.bridge;

import com.google.gson.*;
import java.nio.file.*;
import java.io.*;
import java.security.*;
import java.util.*;

/** Private, default-off causal identity binder. Never creates or moves a card.
 * Recorded numeric identities are names, not outcomes or allocator instructions.
 * Native events retain their actual IDs; each binding is explicit evidence.
 */
public final class ReplayCardIdentities {
 private static ReplayCardIdentities live;
 private final JsonArray births;
 private final Set<Integer> initial=new HashSet<>(), expected=new HashSet<>();
 private final Map<Integer,Integer> forward=new HashMap<>(), reverse=new HashMap<>();
 private final Map<String,Integer> ordinals=new HashMap<>();
 private final Deque<JsonObject> stack=new ArrayDeque<>();
 private int position;
 private static final String TOKEN="forge/game/ability/effects/TokenEffect.resolve(Lforge/game/spellability/SpellAbility;)V";
 private static final Set<String> IDS=Set.of("source_card_id","card_id","attacker_id","land_card_id","target_spell_card_id","selected_card_id");
 private static final Set<String> ARRAYS=Set.of("available_card_ids","selected_card_ids","reveal_card_ids");
 public ReplayCardIdentities(JsonObject tape) {
  if(tape.get("format").getAsInt()!=1)throw new IllegalStateException("Unsupported created identity tape");
  births=tape.getAsJsonArray("births");
  for(JsonElement id:tape.getAsJsonArray("initial_card_ids"))if(!initial.add(integer(id)))throw new IllegalStateException("Duplicate initial identity");
  for(JsonElement entry:births){int id=integer(entry.getAsJsonObject().get("engine_card_id"));if(id<=0||initial.contains(id)||!expected.add(id))throw new IllegalStateException("Ambiguous original created identity");}
 }
 private static int integer(JsonElement value){try{return new java.math.BigDecimal(value.getAsString()).intValueExact();}catch(Exception e){throw new IllegalStateException("Invalid card identity integer",e);}}
 private static ReplayCardIdentities current() {
  String path=System.getProperty("forge.decision.createdIdentityTape");if(path==null)return null;
  if(live!=null)return live;
  try {
   if(!DecisionReplay.enabled()||System.getProperty("forge.referee.replayTape")!=null)throw new IllegalStateException("Created identities require decision replay only");
   if(Files.size(Path.of(path))>1048576)throw new IllegalStateException("Created identity tape exceeds bounded metadata limit");
   byte[] bytes=Files.readAllBytes(Path.of(path));
   if(bytes.length>1048576||!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(System.getProperty("forge.decision.createdIdentitySha256")))throw new IllegalStateException("Created identity tape checksum differs");
   JsonObject tape=JsonParser.parseString(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
   if(!Objects.equals(tape.get("original_sha256").getAsString(),System.getProperty("forge.decision.originalSha256"))||!Objects.equals(tape.get("decisions_sha256").getAsString(),System.getProperty("forge.decision.replaySha256")))throw new IllegalStateException("Created identity source binding differs");
   live=new ReplayCardIdentities(tape);return live;
  }catch(Exception e){throw new IllegalStateException("Created identity initialization failed",e);}
 }
 public static void observe(JsonObject row){ReplayCardIdentities binder=current();if(binder!=null)binder.accept(row);}
 public static JsonObject decision(JsonObject row){ReplayCardIdentities binder=current();return binder==null?row:binder.translate(row);}
 public static void finish(){ReplayCardIdentities binder=current();if(binder!=null)binder.verifyComplete();}
 public void verifyComplete(){if(!stack.isEmpty()||position!=births.size())throw new IllegalStateException("Incomplete created identity reconstruction");}
 public JsonObject translate(JsonObject row){JsonObject copy=row.deepCopy();rewrite(copy);return copy;}
 private int actual(int original){
  if(forward.containsKey(original))return forward.get(original);
  if(expected.contains(original))throw new IllegalStateException("Created identity referenced before validated birth: "+original);
  if(reverse.containsKey(original))throw new IllegalStateException("Unmapped original collides with live created identity: "+original);
  return original;
 }
 private int original(int actual){return reverse.getOrDefault(actual,actual);}
 private void rewrite(JsonElement value){
  if(value.isJsonArray()){for(JsonElement entry:value.getAsJsonArray())rewrite(entry);return;}
  if(!value.isJsonObject())return;
  JsonObject object=value.getAsJsonObject();
  for(String key:new ArrayList<>(object.keySet())){
   JsonElement item=object.get(key);if(item.isJsonNull())continue;
   if(IDS.contains(key))object.addProperty(key,actual(integer(item)));
   else if(ARRAYS.contains(key)){JsonArray ids=new JsonArray();for(JsonElement id:item.getAsJsonArray())ids.add(actual(integer(id)));object.add(key,ids);}
   else if(key.equals("source_ability")){String id=item.getAsString();int colon=id.indexOf(':');if(colon<1)throw new IllegalStateException("Malformed recorded source identity");object.addProperty(key,actual(Integer.parseInt(id.substring(0,colon)))+id.substring(colon));}
   else rewrite(item);
  }
 }
 public void accept(JsonObject row){
  String kind=row.get("kind").getAsString();if(!kind.equals("engine_call")&&!kind.equals("engine_return"))return;
  if(kind.equals("engine_return")){if(stack.isEmpty()||!stack.peek().get("call_id").equals(row.get("call_id"))||!stack.peek().get("hook").equals(row.get("hook")))throw new IllegalStateException("Unpaired created identity event");stack.pop();return;}
  JsonObject frame=new JsonObject();frame.add("call_id",row.get("call_id"));frame.add("hook",row.get("hook"));
  if(row.get("hook").getAsString().equals(TOKEN)){
   JsonObject ability=row.getAsJsonArray("arguments").get(0).getAsJsonObject(),cause=new JsonObject();
   cause.addProperty("source_card_id",original(integer(ability.getAsJsonObject("source").get("card_id"))));cause.add("parameters",ability.get("parameters"));cause.add("turn",row.get("turn"));
   String key=cause.toString();int ordinal=ordinals.merge(key,1,Integer::sum);cause.addProperty("effect_ordinal",ordinal);frame.add("cause",cause);frame.addProperty("birth_count",0);
  }
  stack.push(frame);
  if(!row.get("hook").getAsString().startsWith("forge/game/Game.fireEvent("))return;
  JsonObject event=row.getAsJsonArray("arguments").get(0).getAsJsonObject();
  if(!event.has("record_type")||!event.get("record_type").getAsString().equals("GameEventCardChangeZone")||!event.get("from").isJsonNull()||event.get("to").isJsonNull()||!event.getAsJsonObject("to").get("zoneType").getAsString().equals("Battlefield"))return;
  JsonObject parent=null;for(JsonObject candidate:stack)if(candidate.has("cause")){parent=candidate;break;}if(parent==null)return;
  int ordinal=parent.get("birth_count").getAsInt()+1;parent.addProperty("birth_count",ordinal);JsonObject cause=parent.getAsJsonObject("cause").deepCopy();cause.addProperty("birth_ordinal",ordinal);
  JsonObject card=event.getAsJsonObject("card"),traits=new JsonObject();for(String key:List.of("name","owner","controller","zone","face_down","power","toughness"))traits.add(key,card.get(key));
  if(position>=births.size())throw new IllegalStateException("Unexpected additional token birth");JsonObject entry=births.get(position).getAsJsonObject();
  if(!cause.equals(entry.get("cause"))||!traits.equals(entry.get("characteristics")))throw new IllegalStateException("Created identity cause/characteristics diverged; alias forbidden at "+position);
  int recorded=integer(entry.get("engine_card_id")),actual=integer(card.get("view_id"));
  if(actual<=0||initial.contains(actual)||forward.containsKey(recorded)||reverse.containsKey(actual)||expected.contains(actual)&&actual!=recorded)throw new IllegalStateException("Duplicate/colliding created identity");
  forward.put(recorded,actual);reverse.put(actual,recorded);position++;
  JsonObject binding=new JsonObject();binding.addProperty("original_card_id",recorded);binding.addProperty("replay_card_id",actual);binding.add("cause",cause);binding.addProperty("rules_approved",false);row.add("historical_identity_binding",binding);
 }
}
