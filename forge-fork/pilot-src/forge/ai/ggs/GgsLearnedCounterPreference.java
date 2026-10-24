package forge.ai.ggs;

import com.google.gson.*;
import forge.ai.ComputerUtilAbility;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Opt-in learned local preference. No whole-game utility or default promotion.
 * Scope is the validated three-player MAIN1 diagnostic family, not arbitrary
 * multiplayer threat assessment. Missing, corrupt or out-of-scope inputs retain
 * the stock action. Full-game reward admission is entirely separate.
 */
public final class GgsLearnedCounterPreference {
 private GgsLearnedCounterPreference() {}
 public static double[] features(Player ai, Card target) {
  return new double[]{1.0,target.getController()==ai?1.0:-1.0,target.getNetPower()/10.0,ai.getLife()/40.0};
 }
 public static List<SpellAbility> select(Player ai,List<SpellAbility> stock) {
  String file=System.getProperty("dragonmind.counterPreferenceModel"),expected=System.getProperty("dragonmind.counterPreferenceSha256");
  if(file==null||expected==null||PlannerContext.active()||stock==null||stock.size()!=1||!GgsNinjutsuPolicy.enabled(ai))return stock;
  var game=ai.getGame();SpellAbility counter=stock.get(0);
  if(game.getPlayers().size()!=3||game.getStack().size()!=1||game.getPhaseHandler().getPhase()!=PhaseType.MAIN1
   ||game.getPhaseHandler().isPlayerTurn(ai)||ai.getLife()<30||ai.getLife()>40||!counter.isSpell()
   ||counter.getApi()!=ApiType.Counter||!counter.getHostCard().getName().equals("Swan Song"))return stock;
  SpellAbility removal=ComputerUtilAbility.getTopSpellAbilityOnStack(game,counter);
  if(removal==null||!removal.isSpell()||removal.getApi()!=ApiType.Destroy||removal.getSubAbility()!=null
    ||removal.getActivatingPlayer()==null||!removal.getActivatingPlayer().isOpponentOf(ai)
    ||removal.getTargets().getTargetCards().size()!=1)return stock;
  Card target=removal.getTargets().getTargetCards().get(0);
  if(!target.isCreature()||target.getNetPower()<0||target.getNetPower()>6||target.isFaceDown()||target.isPhasedOut())return stock;
  // Cross-player continuous restrictions are outside the supervised family.
  // Preserve stock, for example, when the opposing target prevents attacks.
  if(target.getStaticAbilities().stream().anyMatch(s->s.hasParam("ValidCard")||s.hasParam("ValidPlayer")
    ||s.hasParam("Affected")&&!s.getParam("Affected").contains("YouCtrl")&&!s.getParam("Affected").equals("Card.Self")))return stock;
  try {
   byte[] data=Files.readAllBytes(Path.of(file));
   String actual=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));
   if(!actual.equals(expected))return stock;
   JsonObject model=JsonParser.parseString(new String(data,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
   if(model.get("format").getAsInt()!=1||!model.get("scope").getAsString().equals("scoped_counterspell_preference_v1"))return stock;
   JsonArray names=model.getAsJsonArray("features"),weights=model.getAsJsonArray("weights");
   String[] expectedNames={"bias","own_target","target_power_scaled","life_scaled"};
   double[] f=features(ai,target);double z=0;
   if(names.size()!=4||weights.size()!=4)return stock;
   for(int i=0;i<4;i++) {
    if(!names.get(i).getAsString().equals(expectedNames[i]))return stock;
    double w=weights.get(i).getAsDouble();if(!Double.isFinite(w)||Math.abs(w)>100)return stock;z+=w*f[i];
   }
   double probability=1/(1+Math.exp(-Math.max(-40,Math.min(40,z))));
   return probability<0.25?null:stock;
  } catch(Exception invalidModel) { return stock; }
 }
}
