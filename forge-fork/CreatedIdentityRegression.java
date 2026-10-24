import com.google.gson.*;
import forge.ai.bridge.ReplayCardIdentities;

/** Exercises the production binder; no engine outcomes or legality certified. */
public final class CreatedIdentityRegression {
 static JsonObject object(String value){return JsonParser.parseString(value).getAsJsonObject();}
 static void rejected(Runnable action,String text){try{action.run();throw new AssertionError("Accepted "+text);}catch(IllegalStateException e){if(!e.getMessage().contains(text))throw e;}}
 public static void main(String[] args){
  JsonObject cause=object("{source_card_id:242,parameters:{TokenScript:u_2_2_bird_flying,TokenOwner:TargetedController,DB:Token},turn:8,effect_ordinal:1,birth_ordinal:1}"),traits=object("{name:'Bird Token',owner:3,controller:3,zone:Battlefield,face_down:false,power:2,toughness:2}");
  JsonObject entry=new JsonObject();entry.addProperty("engine_card_id",412);entry.add("cause",cause);entry.add("characteristics",traits);
  JsonObject tape=object("{format:1,initial_card_ids:[242]}");JsonArray entries=new JsonArray();entries.add(entry);tape.add("births",entries);
  JsonObject choice=object("{source_card_id:412,source_ability:'412:99',selected_card_ids:[412],actor_id:412,context:{priority_player_id:412}}");
  ReplayCardIdentities valid=new ReplayCardIdentities(tape);
  rejected(valid::verifyComplete,"Incomplete created identity");
  rejected(()->valid.translate(choice),"before validated birth");
  JsonObject effect=object("{kind:engine_call,call_id:1,hook:'forge/game/ability/effects/TokenEffect.resolve(Lforge/game/spellability/SpellAbility;)V',turn:8,arguments:[{source:{card_id:242},parameters:{TokenScript:u_2_2_bird_flying,TokenOwner:TargetedController,DB:Token}}]}");
  JsonObject birth=object("{kind:engine_call,call_id:2,hook:'forge/game/Game.fireEvent(Lforge/game/event/GameEvent;)V',arguments:[{record_type:GameEventCardChangeZone,from:null,to:{zoneType:Battlefield}}]}");
  JsonObject card=traits.deepCopy();card.addProperty("view_id",406);birth.getAsJsonArray("arguments").get(0).getAsJsonObject().add("card",card);
  valid.accept(effect.deepCopy());valid.accept(birth);
  JsonObject translated=valid.translate(choice);if(translated.get("source_card_id").getAsInt()!=406||!translated.get("source_ability").getAsString().equals("406:99")||translated.getAsJsonArray("selected_card_ids").get(0).getAsInt()!=406||translated.get("actor_id").getAsInt()!=412||translated.getAsJsonObject("context").get("priority_player_id").getAsInt()!=412||choice.get("source_card_id").getAsInt()!=412||!birth.has("historical_identity_binding"))throw new AssertionError("Typed translation or evidence mutation");
  rejected(()->valid.translate(object("{source_card_id:406}")),"collides");
  rejected(()->valid.accept(birth.deepCopy()),"additional token birth");
  for(String key:new String[]{"owner","power"}){
   ReplayCardIdentities bad=new ReplayCardIdentities(tape);bad.accept(effect.deepCopy());JsonObject wrong=birth.deepCopy();wrong.getAsJsonArray("arguments").get(0).getAsJsonObject().getAsJsonObject("card").addProperty(key,99);rejected(()->bad.accept(wrong),"characteristics diverged");
  }
  ReplayCardIdentities wrongCause=new ReplayCardIdentities(tape);JsonObject wrong=effect.deepCopy();wrong.addProperty("turn",9);wrongCause.accept(wrong);rejected(()->wrongCause.accept(birth.deepCopy()),"cause/characteristics diverged");
  JsonObject duplicate=tape.deepCopy();duplicate.getAsJsonArray("births").add(entry);rejected(()->new ReplayCardIdentities(duplicate),"Ambiguous original");
  ReplayCardIdentities terminal=new ReplayCardIdentities(tape);terminal.accept(effect.deepCopy());terminal.accept(birth.deepCopy());
  terminal.accept(object("{kind:engine_return,call_id:2,hook:'forge/game/Game.fireEvent(Lforge/game/event/GameEvent;)V'}"));
  terminal.accept(object("{kind:engine_return,call_id:1,hook:'forge/game/ability/effects/TokenEffect.resolve(Lforge/game/spellability/SpellAbility;)V'}"));terminal.verifyComplete();
  System.out.println("PASS causal birth, explicit binding, immutable choices, typed card-only translation, before-birth/collision/duplicate/cause/owner/PT rejection; not rules approval");
 }
}
