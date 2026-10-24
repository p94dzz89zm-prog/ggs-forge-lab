import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;

/** Engine transitions, not synthetic owner/controller dictionaries. */
public class OwnershipEvidenceRegression extends AITest {
 int checks;
 void identities(Card c,Player owner,Player controller){var j=BridgeSnapshot.entity(c,owner);Assert.assertEquals(j.get("owner_id").getAsInt(),owner.getId());Assert.assertEquals(j.get("controller_id").getAsInt(),controller.getId());checks++;}
 void run(){
  Game g=initAndCreateThreePlayerGame();Player owner=g.getPlayers().get(0),thief=g.getPlayers().get(1),third=g.getPlayers().get(2);for(Player p:g.getPlayers())fillLibrary(p,20);
  Card c=addCard("Runeclaw Bear",owner);identities(c,owner,owner);
  c.addTempController(thief,g.getNextTimestamp());g.getAction().controllerChangeZoneCorrection(c);identities(c,owner,thief);
  c.phase(true);Assert.assertTrue(c.isPhasedOut());identities(c,owner,thief);
  String view=BridgeSnapshot.forPlayer(third).toString();Assert.assertTrue(view.contains("Runeclaw Bear"),"phased-out public object missing");checks++;
  c.phase(false);c=g.getAction().moveToGraveyard(c,null);identities(c,owner,owner);Assert.assertEquals(BridgeSnapshot.entity(c,owner).get("zone").getAsString(),"Graveyard");checks++;
  Card secret=addCardToZone("Demonic Tutor",owner,ZoneType.Hand);Assert.assertFalse(BridgeSnapshot.forPlayer(thief).toString().contains("Demonic Tutor"));checks++;
  Card facedown=addCard("Fallen Shinobi",owner);facedown.turnFaceDown(true);Assert.assertFalse(BridgeSnapshot.entity(facedown,thief).toString().contains("Fallen Shinobi"));identities(facedown,owner,owner);
  Card commander=addCard("Goro-Goro and Satoru",owner);commander.setCommander(true);commander.addTempController(thief,g.getNextTimestamp());g.getAction().controllerChangeZoneCorrection(commander);identities(commander,owner,thief);
  g.getAction().moveToCommand(commander,null);Card returned=owner.getCardsIn(ZoneType.Command).stream().filter(Card::isCommander).findFirst().orElseThrow();identities(returned,owner,owner);Assert.assertTrue(BridgeSnapshot.entity(returned,owner).get("commander").getAsBoolean());checks++;
  for(int mode=0;mode<3;mode++){
   g=initAndCreateThreePlayerGame();owner=g.getPlayers().get(0);thief=g.getPlayers().get(1);for(Player p:g.getPlayers())fillLibrary(p,20);
   c=addCard("Runeclaw Bear",owner);c.addTempController(thief,g.getNextTimestamp());g.getAction().controllerChangeZoneCorrection(c);
   if(mode==2)c.phase(true);
   Player departing=mode==0?thief:owner;departing.loseConditionMet(GameLossReason.Conceded,null);g.onPlayerLost(departing);
   Assert.assertFalse(g.getPlayers().contains(departing));
   if(mode==0){Assert.assertTrue(c.isInZone(ZoneType.Battlefield));identities(c,owner,owner);}
   else {for(Player survivor:g.getPlayers())Assert.assertFalse(survivor.getCardsIn(ZoneType.Battlefield,false).contains(c),"departed owner object remains");checks++;}
  }
  System.out.println("Checks passed: "+checks);System.out.println("PASS ownership evidence, control change, graveyard, phasing, visibility and actual elimination");
 }
 public static void main(String[]args)throws Exception{OwnershipEvidenceRegression t=new OwnershipEvidenceRegression();t.initializeModel();t.run();System.exit(0);}
}
