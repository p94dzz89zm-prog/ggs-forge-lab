import forge.ai.*;
import forge.ai.bridge.*;
import forge.card.ColorSet;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.replacement.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import com.google.gson.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Actual engine offered-object rebinding; no outcomes applied by the driver. */
public class EffectReplayRegression extends AITest {
 static JsonObject trait(ReplacementEffect effect){JsonObject row=new JsonObject();row.addProperty("trait_type",effect.getClass().getName());row.addProperty("source_card_id",effect.getHostCard().getId());JsonObject p=new JsonObject();effect.getMapParams().forEach(p::addProperty);row.add("parameters",p);return row;}
 static JsonObject row(Player p,String hook,String kind,int index){JsonObject r=new JsonObject();r.addProperty("kind","decision");r.addProperty("index",index);r.addProperty("actor_id",p.getId());r.addProperty("hook",p.getController().getClass().getName().replace('.','/')+hook);r.addProperty("decision_type",kind);return r;}
 static void source(JsonObject row,SpellAbility ability){row.addProperty("source_ability",ability.getHostCard().getId()+":"+ability.getId());}
 public static void main(String[] args)throws Exception{
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);EffectReplayRegression test=new EffectReplayRegression();test.initializeModel();Game game=test.initAndCreateThreePlayerGame();Player player=game.getPlayers().get(1);
  for(Player p:game.getPlayers())test.fillLibrary(p,10);
  Card glade=test.addCardToZone("Cinder Glade",player,ZoneType.Hand);List<ReplacementEffect> effects=new ArrayList<>();for(ReplacementEffect e:glade.getReplacementEffects())effects.add(e);if(effects.size()!=1)throw new AssertionError("Expected one Cinder replacement");
  Card hydra=test.addCardToZone("Voracious Hydra",player,ZoneType.Hand);SpellAbility counterAbility=null;for(ReplacementEffect e:hydra.getReplacementEffects()){SpellAbility sa=e.ensureAbility();if(sa!=null&&"PutCounter".equals(String.valueOf(sa.getApi())))counterAbility=sa;}if(counterAbility==null)throw new AssertionError("Missing actual Hydra counter replacement ability");
  Card grove=test.addCardToZone("Thriving Grove",player,ZoneType.Hand);SpellAbility colorAbility=null;for(ReplacementEffect e:grove.getReplacementEffects()){SpellAbility sa=e.ensureAbility();if(sa!=null&&"ChooseColor".equals(String.valueOf(sa.getApi())))colorAbility=sa;}if(colorAbility==null)throw new AssertionError("Missing actual Grove color ability");
  List<JsonObject> rows=new ArrayList<>();
  JsonObject a=row(player,".chooseSingleReplacementEffect(Ljava/util/List;)Lforge/game/replacement/ReplacementEffect;","replacement_choice",0);JsonArray offered=new JsonArray();effects.forEach(e->offered.add(trait(e)));a.add("available_effects",offered);a.add("selected_effect",trait(effects.get(0)));rows.add(a);
  JsonObject b=row(player,".chooseCounterType(Ljava/util/List;Lforge/game/spellability/SpellAbility;Ljava/lang/String;Ljava/util/Map;)Lforge/game/card/CounterType;","counter_choice",1);source(b,counterAbility);b.addProperty("title","Select counter type");JsonArray counters=new JsonArray();counters.add("P1P1");b.add("available_counters",counters);b.addProperty("selected_counter",mode.equals("bad-counter")?"M1M1":"P1P1");JsonArray keys=new JsonArray();keys.add("Target");b.add("null_parameter_keys",keys);rows.add(b);
  JsonObject c=row(player,".chooseColors(Ljava/lang/String;Lforge/game/spellability/SpellAbility;IILforge/card/ColorSet;)Lforge/card/ColorSet;","color_choice",2);source(c,colorAbility);c.addProperty("title","Choose a color");c.addProperty("min",1);c.addProperty("max",1);c.addProperty("allowed_colors","WUBR");c.addProperty("selected_colors",mode.equals("bad-color")?"G":"B");rows.add(c);
  if(mode.equals("bad-replacement"))a.getAsJsonObject("selected_effect").addProperty("source_card_id",999999);
  JsonObject end=new JsonObject();end.addProperty("kind","decision_tape_complete");end.addProperty("decisions",3);StringBuilder text=new StringBuilder();for(JsonObject r:rows)text.append(r).append('\n');text.append(end).append('\n');Path tape=root.resolve("decisions.jsonl");Files.writeString(tape,text.toString(),StandardOpenOption.CREATE_NEW);
  System.setProperty("forge.decision.replayTape",tape.toString());System.setProperty("forge.decision.replaySha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try{
   if(player.getController().chooseSingleReplacementEffect(effects)!=effects.get(0))throw new AssertionError("Replacement not rebound to offered live object");
   Map<String,Object> params=new HashMap<>();params.put("Target",null);if(player.getController().chooseCounterType(List.of(CounterEnumType.P1P1),counterAbility,"Select counter type",params)!=CounterEnumType.P1P1)throw new AssertionError("Counter changed");
   if(player.getController().chooseColors("Choose a color",colorAbility,1,1,ColorSet.WUBR)!=ColorSet.B)throw new AssertionError("Color changed");
   if(!mode.equals("valid"))throw new AssertionError("Invalid choice accepted");DecisionReplay.finish();
   if(!glade.isInZone(ZoneType.Hand)||hydra.getCounters(CounterEnumType.P1P1)!=0||(grove.getChosenColors()!=null&&grove.getChosenColors().iterator().hasNext()))throw new AssertionError("Driver applied a recorded outcome");
   System.out.println("PASS live Cinder replacement, Hydra counter and Grove excluded-color choices; no outcomes copied");
  }catch(IllegalStateException expected){
   if(mode.equals("valid")||!expected.getMessage().contains("Illegal recorded"))throw expected;
   long index=mode.equals("bad-replacement")?0:mode.equals("bad-counter")?1:2;if(!Files.exists(root.resolve("diagnostics/decision-failure-"+index+".json")))throw new AssertionError("Missing diagnostic");
   try{DecisionReplay.finish();throw new AssertionError("Failed replay completed");}catch(IllegalStateException rejected){if(!rejected.getMessage().contains("failed decision"))throw rejected;}
   System.out.println("PASS "+mode+" rejected; offered-domain diagnostic retained; completion denied");
  }
  System.exit(0);
 }
}
