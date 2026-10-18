import forge.ai.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Real stock choice and actual automatic payment; synthetic public position. */
public class WhipManaReservationRegression extends PackageRecoveryRegression {
 void scenario(boolean reserve,boolean candidate){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1);for(Player p:g.getPlayers())fillLibrary(p,30);ai.setLife(7,null);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  for(String n:List.of("Swamp","Swamp","Swamp","Swamp","Island","Island","Island","Mountain"))addCard(n,ai);
  addCard("Goro-Goro and Satoru",ai);addToken("r_5_5_dragon_spirit_flying",ai);
  Card whip=addCardToZone("Whip of Erebos",ai,ZoneType.Hand),grave=addCardToZone("Baleful Strix",ai,ZoneType.Graveyard);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  var controller=((PlayerControllerAi)ai.getController()).getAi();var choices=controller.chooseSpellAbilityToPlay();System.out.println("RESERVE stock="+choices);Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);Assert.assertEquals(choices.get(0).getHostCard(),whip,"actual stock chooses Whip");
  if(reserve){int n=0;for(Card land:ai.getLandsInPlay())if(land.getName().equals("Swamp")&&n++<2)controller.getCardMemory().rememberCard(land,AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);}
  play(ai,choices.get(0));Card resolved=ai.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getName().equals("Whip of Erebos")).findFirst().orElseThrow();
  // The next real decision clears one-spell reservations, as normal.
  var next=controller.chooseSpellAbilityToPlay();System.out.println("RESERVE next="+next+" untappedBlack="+ai.getLandsInPlay().stream().filter(c->!c.isTapped()&&c.getName().equals("Swamp")).count());
  SpellAbility rise=resolved.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElseThrow();rise.setActivatingPlayer(ai);rise.getTargets().add(grave);
  Assert.assertEquals(ComputerUtilCost.canPayCost(rise,ai,false),reserve||candidate);
  if(reserve||candidate){play(ai,rise);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),8L);Assert.assertTrue(ai.getCreaturesInPlay().stream().anyMatch(c->c.getName().equals("Baleful Strix")));}
  groups++;System.out.println("RESERVE manual="+reserve+" paidRecovery="+(reserve||candidate));
 }
 public static void main(String[]args){var t=new WhipManaReservationRegression();t.initializeModel();boolean candidate=Boolean.parseBoolean(args[0]);t.scenario(false,candidate);t.scenario(true,candidate);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
