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
/** Constructed established mana bases; every land is in listed Apex100. */
public class WhipMixedLandProbe extends PackageRecoveryRegression {
 void probe(int id,List<String> lands){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1);for(Player p:g.getPlayers())fillLibrary(p,30);ai.setLife(7,null);if(id==8)addCard("Island",g.getPlayers().get(2));System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  for(String n:lands){Card land=addCard(n,ai);land.setTapped(false);land.setTurnInZone(-1);}Card leader=addCard("Goro-Goro and Satoru",ai);leader.setCommander(true);ai.addCommander(leader);ai.initCommanderColor(leader);addToken("r_5_5_dragon_spirit_flying",ai);Card whip=addCardToZone("Whip of Erebos",ai,ZoneType.Hand),grave=addCardToZone("Baleful Strix",ai,ZoneType.Graveyard);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  var controller=((PlayerControllerAi)ai.getController()).getAi();var choices=controller.chooseSpellAbilityToPlay();Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);Assert.assertEquals(choices.get(0).getHostCard(),whip);play(ai,choices.get(0));controller.chooseSpellAbilityToPlay();Card resolved=ai.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getName().equals("Whip of Erebos")).findFirst().orElseThrow();SpellAbility rise=resolved.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElseThrow();rise.setActivatingPlayer(ai);rise.getTargets().add(grave);boolean payable=ComputerUtilCost.canPayCost(rise,ai,false);if(payable)play(ai,rise);groups++;System.out.println("MIXED_PROBE case="+id+" payable="+payable+" life="+ai.getLife()+" untapped="+ai.getLandsInPlay().stream().filter(c->!c.isTapped()).map(Card::getName).toList());
 }
 public static void main(String[]args){var t=new WhipMixedLandProbe();t.initializeModel();t.probe(0,List.of("Swamp","Blood Crypt","Watery Grave","Raucous Theater","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(1,List.of("Swamp","Undercity Sewers","Xander's Lounge","Blood Crypt","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(2,List.of("Blazemire Verge","Gloomlake Verge","Command Tower","Mana Confluence","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(3,List.of("Reflecting Pool","Exotic Orchard","Command Tower","Training Center","Morphic Pool","Luxury Suite","Island","Mountain"));t.probe(4,List.of("Swamp","Shizo, Death's Storehouse","Takenuma, Abandoned Mire","Gloomlake Verge","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(5,List.of("Swamp","Shizo, Death's Storehouse","Takenuma, Abandoned Mire","Blazemire Verge","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(6,List.of("Shizo, Death's Storehouse","Takenuma, Abandoned Mire","Command Tower","Morphic Pool","Island","Mountain","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(7,List.of("Swamp","Shizo, Death's Storehouse","Takenuma, Abandoned Mire","Undercity Sewers","Command Beacon","Island","Otawara, Soaring City","Sokenzan, Crucible of Defiance"));t.probe(8,List.of("Reflecting Pool","Exotic Orchard","Command Tower","Training Center","Morphic Pool","Luxury Suite","Island","Mountain"));System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
