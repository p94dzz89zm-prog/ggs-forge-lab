import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Actual casts and payment across different bodies/ETBs, not canned score labels. */
public class SneakVarietyRegression extends AITest {
 void scenario(String name,int seed) {
  forge.util.MyRandom.setRandom(new Random(seed));Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",List.of("BALANCED","ENGINE","ECONOMY").get(seed%3));
  Card engine=addCard("Goro-Goro and Satoru",ai);engine.setCommander(true);addCard("Ninja Teen",ai).setClassLevel(3);
  Card carrier=addCard("Changeling Outcast",ai);carrier.setSickness(false);carrier.setTurnInZone(-1);
  Card incoming=addCardToZone(name,ai,ZoneType.Graveyard);int id=incoming.getId();
  for(int i=0;i<4;i++)addCard("Swamp",ai);fillLibrary(ai,40);fillLibrary(opp,40);
  g.getAction().checkStateEffects(true);g.getTriggerHandler().resetActiveTriggers();
  Combat combat=new Combat(ai);combat.addAttacker(carrier,opp);combat.setBlocked(carrier,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  SpellAbility cast=ComputerUtilAbility.getSpellAbilities(new CardCollection(incoming),ai).stream().filter(SpellAbility::isSneak).findFirst().orElseThrow();cast.setActivatingPlayer(ai);
  Assert.assertTrue(((PlayerControllerAi)ai.getController()).getAi().canPlaySa(cast).willingToPlay(),name+" strategic willingness");
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null),name+" actual payment");
  for(int i=0;i<50;i++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())break;g.getStack().resolveStack();if(i==49)throw new AssertionError("Stack did not drain");}
  Card actual=ai.getCreaturesInPlay().stream().filter(c->c.getId()==id).findFirst().orElseThrow();
  Assert.assertTrue(carrier.isInZone(ZoneType.Hand));Assert.assertTrue(engine.isInZone(ZoneType.Battlefield));Assert.assertTrue(combat.isAttacking(actual));Assert.assertTrue(actual.enteredThisTurn());
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),4L);
  Assert.assertEquals(opp.getLife(),19,"Ninja Teen's leave trigger resolves in Constructed fixture");
  System.out.println("PASS actual Sneak card="+name+" seed="+seed);
 }
 public static void main(String[]args){SneakVarietyRegression t=new SneakVarietyRegression();t.initializeModel();
  var names=List.of("Moon-Circuit Hacker","Ninja of the Deep Hours","Mistblade Shinobi","Nezumi Prowler","Orochi Soul-Reaver","Fallen Shinobi","Ingenious Infiltrator","Prosperous Thief","Baleful Strix","Faerie Seer","Krenko, Tin Street Kingpin","Balefire Dragon","Professional Face-Breaker","Terror of the Peaks","Ragavan, Nimble Pilferer","Karlach, Fury of Avernus","Port Razer","Tetsuko Umezawa, Fugitive");
  int count=0;for(String name:names){t.scenario(name,8100+count);count++;}System.out.println("Checks passed: "+count);System.exit(0);
 }
}
