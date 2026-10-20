import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import com.google.gson.*;
import org.testng.Assert;
import java.util.*;
/** Actual mana activation, snapshot contents and floating-mana spell payment. */
public class PlannerManaAuditRegression extends AITest {
 static JsonObject pool(Player p){for(var row:PlannerSnapshot.forPlayer(p).getAsJsonArray("public_mana_pools"))if(row.getAsJsonObject().get("player_id").getAsInt()==p.getId())return row.getAsJsonObject();throw new AssertionError("missing mana pool");}
 public static void main(String[]args){PlannerManaAuditRegression t=new PlannerManaAuditRegression();t.initializeModel();int checks=0;Game g=t.initAndCreateThreePlayerGame();Player p=g.getPlayers().get(1);for(Player s:g.getPlayers())t.fillLibrary(s,12);
  Card island=t.addCard("Island",p),mountain=t.addCard("Mountain",p),kari=t.addCardToZone("Kari Zev, Skyship Raider",p,ZoneType.Hand);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,p,false,4);
  Assert.assertEquals(pool(p).get("total").getAsInt(),0);Assert.assertFalse(pool(p).has("pool"));checks++;
  for(Card land:List.of(island,mountain)){var mana=land.getManaAbilities().get(0);mana.setActivatingPlayer(p);Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,mana,null));LinePlannerRegression.drain(g);Assert.assertTrue(land.isTapped());}
  JsonObject value=pool(p);Assert.assertEquals(value.get("total").getAsInt(),2);Assert.assertEquals(value.getAsJsonObject("colors").get("U").getAsInt(),1);Assert.assertEquals(value.getAsJsonObject("colors").get("R").getAsInt(),1);Assert.assertEquals(value.getAsJsonArray("units").size(),2);for(var unit:value.getAsJsonArray("units")){Assert.assertTrue(unit.getAsJsonObject().has("source_card_id"));Assert.assertTrue(unit.getAsJsonObject().has("restricted"));}checks++;
  var spell=kari.getFirstSpellAbility();spell.setActivatingPlayer(p);Assert.assertTrue(ComputerUtilCost.canPayCost(spell,p,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,spell,null));LinePlannerRegression.drain(g);Assert.assertTrue(p.getCreaturesInPlay().stream().anyMatch(c->c.getId()==kari.getId()));Assert.assertEquals(pool(p).get("total").getAsInt(),0);Assert.assertEquals(pool(p).getAsJsonArray("units").size(),0);checks++;
  System.out.println("Checks passed: "+checks);System.exit(0);
 }
}
