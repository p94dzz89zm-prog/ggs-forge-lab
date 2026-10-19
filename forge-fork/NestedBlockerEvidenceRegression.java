import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.event.*;
import com.google.common.collect.*;
import com.google.gson.*;
import java.util.*;

/** Reproduce the exact real-game nested blocker owner/controller depth gap. */
public class NestedBlockerEvidenceRegression extends AITest {
 public static void main(String[] args)throws Exception {
  NestedBlockerEvidenceRegression test=new NestedBlockerEvidenceRegression();test.initializeModel();
  Game game=test.initAndCreateThreePlayerGame();Player attacker=game.getPlayers().get(0),defender=game.getPlayers().get(1);
  Card bear=test.addCard("Runeclaw Bear",attacker),blocker=test.addCard("Grizzly Bears",defender);
  Multimap<Card,Card> blocks=HashMultimap.create();blocks.put(bear,blocker);
  GameEventBlockersDeclared event=new GameEventBlockersDeclared(defender,Map.of(defender,blocks));
  var encode=EngineEvidence.class.getDeclaredMethod("value",Object.class,int.class);encode.setAccessible(true);
  // The actual event is an element of the engine_call.arguments array.
  JsonObject row=((JsonElement)encode.invoke(null,new Object[]{event},0)).getAsJsonArray().get(0).getAsJsonObject();
  String text=row.toString();boolean old=args.length>0&&args[0].equals("--expect-truncated");
  if(old){if(!text.contains("unencoded"))throw new AssertionError("Old control did not reproduce missing leaf");System.out.println("PASS old nested-blocker depth truncation reproduced");}
  else {
   if(text.contains("unencoded"))throw new AssertionError("Nested blocker identity truncated: "+text);
   JsonObject card=row.getAsJsonObject("blockers").getAsJsonArray("map_entries").get(0).getAsJsonObject().getAsJsonObject("value").getAsJsonArray("map_entries").get(0).getAsJsonObject().getAsJsonArray("value").get(0).getAsJsonObject();
   if(card.getAsJsonObject("owner").get("view_id").getAsInt()!=defender.getId()||card.getAsJsonObject("controller").get("view_id").getAsInt()!=defender.getId())throw new AssertionError("Wrong blocker owner/controller");
   System.out.println("PASS nested blocker owner/controller identities retained without expanding player graph");
  }
  System.exit(0);
 }
}
