import forge.ai.*;
import forge.ai.bridge.BridgeSnapshot;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.zone.*;
import com.google.gson.*;
import org.testng.Assert;
import java.util.List;

/** Review gaps discovered in sealed games: public state, never hidden identities. */
public class SnapshotEvidenceRegression extends AITest {
 public static void main(String[]args)throws Exception {
  SnapshotEvidenceRegression t=new SnapshotEvidenceRegression();t.initializeModel();Game g=t.initAndCreateThreePlayerGame();Player me=g.getPlayers().get(1),other=g.getPlayers().get(0);
  Card body=t.addCard("Unstoppable Slasher",me);body.setCounters(CounterEnumType.STUN,2);body.setDamage(1);
  JsonObject j=BridgeSnapshot.entity(body,other);Assert.assertEquals(j.getAsJsonObject("counters").get(CounterEnumType.STUN.getName()).getAsInt(),2);Assert.assertEquals(j.get("marked_damage").getAsInt(),1);
  Card land=t.addCard("Thriving Grove",me);land.setChosenColors(List.of("Red"));Assert.assertEquals(BridgeSnapshot.entity(land,other).getAsJsonArray("chosen_colors").get(0).getAsString(),"Red");
  Card commander=t.addCard("Goro-Goro and Satoru",me);commander.setCommander(true);me.addCommander(commander);me.incCommanderCast(commander);other.addCommanderDamage(commander,6);
  JsonArray players=BridgeSnapshot.forPlayer(me).getAsJsonArray("players");JsonObject own=null,opponent=null;for(JsonElement entry:players){JsonObject p=entry.getAsJsonObject();if(p.get("id").getAsInt()==me.getId())own=p;if(p.get("id").getAsInt()==other.getId())opponent=p;}
  Assert.assertEquals(own.getAsJsonObject("commander_casts").get(String.valueOf(commander.getId())).getAsInt(),1);Assert.assertEquals(opponent.getAsJsonObject("commander_damage").get(String.valueOf(commander.getId())).getAsInt(),6);
  Card secret=t.addCardToZone("Demonic Tutor",other,ZoneType.Hand);Assert.assertFalse(BridgeSnapshot.forPlayer(me).toString().contains(secret.getName()));
  body.turnFaceDown(true);j=BridgeSnapshot.entity(body,other);Assert.assertFalse(j.toString().contains("Unstoppable Slasher"));Assert.assertEquals(j.getAsJsonObject("counters").get(CounterEnumType.STUN.getName()).getAsInt(),2);
  System.out.println("Checks passed: 7");System.out.println("PASS counters,damage,chosen-color,commander-cast/damage and visibility evidence");System.exit(0);
 }
}
