package forge.ai.ggs;

import com.google.gson.*;
import forge.game.ability.ApiType;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Opt-in fitted threat contrast; no incumbent promotion or game-value model. */
public final class GgsMultiplayerCounterPreference {
 private GgsMultiplayerCounterPreference() {}
 public static List<SpellAbility> select(Player ai,List<SpellAbility> stock) {
  String path=System.getProperty("dragonmind.multiplayerCounterModel"),hash=System.getProperty("dragonmind.multiplayerCounterSha256");
  if(path==null||hash==null||PlannerContext.active()||!GgsNinjutsuPolicy.enabled(ai)||stock==null||stock.size()!=1)return stock;
  var game=ai.getGame();SpellAbility counter=stock.get(0);
  if(game.getPlayers().size()!=4||game.getStack().size()!=1||game.getPhaseHandler().getPhase()!=PhaseType.MAIN1
   ||game.getPhaseHandler().isPlayerTurn(ai)||ai.getLife()<=0||ai.getLife()>40
   ||counter.getApi()!=ApiType.Counter||!counter.isSpell()||!counter.getHostCard().getName().equals("Swan Song"))return stock;
  SpellAbility top=game.getStack().peekAbility();
  if(top==null||!top.isSpell()||top.getApi()!=ApiType.Destroy||top.getSubAbility()!=null
   ||top.getActivatingPlayer()==null||!top.getActivatingPlayer().isOpponentOf(ai)
   ||top.getTargets().getTargetCards().size()!=1)return stock;
  var target=top.getTargets().getTargetCards().get(0);
  if(!target.isCreature()||target.isFaceDown()||target.isPhasedOut())return stock;
  try {
   byte[] bytes=Files.readAllBytes(Path.of(path));
   if(!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)).equals(hash))return stock;
   JsonObject model=JsonParser.parseString(new String(bytes,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
   if(model.get("format").getAsInt()!=1||!model.get("scope").getAsString().equals("four_player_visible_survival_v1"))return stock;
   JsonArray names=model.getAsJsonArray("features"),weights=model.getAsJsonArray("weights");
   if(names.size()!=2||weights.size()!=2||!names.get(0).getAsString().equals("bias")||!names.get(1).getAsString().equals("public_lethal_exposure_delta"))return stock;
   double[] f=GgsMultiplayerCounterFeatures.extract(ai);if(f==null||f[1]==0)return stock;
   double z=0;for(int i=0;i<2;i++){double w=weights.get(i).getAsDouble();if(!Double.isFinite(w)||Math.abs(w)>100)return stock;z+=w*f[i];}
   return 1/(1+Math.exp(-Math.max(-40,Math.min(40,z))))<.25?null:stock;
  }catch(Exception unsupported){return stock;}
 }
}
