import forge.ai.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.Keyword;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;

/** Constructed paid recovery interactions; no full-game certification. */
public class PackageRecoveryRegression extends TetsukoLifelinkRegression {
 void play(Player p,SpellAbility sa){sa.setActivatingPlayer(p);Assert.assertTrue(sa.canPlay(),"timing legality");Assert.assertTrue(ComputerUtilCost.canPayCost(sa,p,false),"payable cost");Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(p,sa,null),"actual payment");drain(p.getGame());}
 Card permanent(Player p,String name){return p.getCreaturesInPlay().stream().filter(c->c.getName().equals(name)).findFirst().orElseThrow();}
 void victimize(){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);
  Card sacrifice=addCard("Gingerbrute",ai),a=addCardToZone("Baleful Strix",ai,ZoneType.Graveyard),b=addCardToZone("Fire Navy Trebuchet",ai,ZoneType.Graveyard);
  for(int i=0;i<3;i++)addCard("Swamp",ai);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  Card spell=addCardToZone("Victimize",ai,ZoneType.Hand);SpellAbility sa=spell.getFirstSpellAbility();sa.setActivatingPlayer(ai);SpellAbility rise=sa.getSubAbility();rise.setActivatingPlayer(ai);
  Assert.assertTrue(rise.canTarget(a));Assert.assertTrue(rise.canTarget(b));Assert.assertFalse(rise.canTarget(sacrifice),"sacrifice still on battlefield when targets chosen");rise.getTargets().add(a);rise.getTargets().add(b);
  play(ai,sa);
  Assert.assertTrue(ai.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getName().equals("Gingerbrute")),"sacrifice at resolution");
  Card strix=permanent(ai,"Baleful Strix"),trebuchet=permanent(ai,"Fire Navy Trebuchet");Assert.assertTrue(strix.isTapped());Assert.assertTrue(trebuchet.isTapped());Assert.assertTrue(strix.enteredThisTurn());Assert.assertFalse(CombatUtil.canAttack(strix,opp),"tapped recovery does not immediately attack");
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);groups++;System.out.println("PACKAGE Victimize paid3 twoTargets sacrificedOnResolution returnedTapped=true");
 }
 void whipExile(){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);
  for(int i=0;i<8;i++)addCard("Swamp",ai);for(int i=0;i<2;i++)addCard("Swamp",opp);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  Card whip=cast(ai,addCardToZone("Whip of Erebos",ai,ZoneType.Hand)),grave=addCardToZone("Ragavan, Nimble Pilferer",ai,ZoneType.Graveyard);
  SpellAbility returner=whip.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElseThrow();returner.setActivatingPlayer(ai);Assert.assertTrue(returner.canTarget(grave));returner.getTargets().add(grave);play(ai,returner);
  Card ragavan=permanent(ai,"Ragavan, Nimble Pilferer");Assert.assertTrue(ragavan.hasKeyword(Keyword.HASTE));Assert.assertTrue(ragavan.hasKeyword(Keyword.LIFELINK));Assert.assertTrue(whip.isTapped());Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),8L);
  SpellAbility kill=addCardToZone("Doom Blade",opp,ZoneType.Hand).getFirstSpellAbility();kill.setActivatingPlayer(opp);Assert.assertTrue(kill.canTarget(ragavan));kill.getTargets().add(ragavan);play(opp,kill);
  Assert.assertTrue(ai.getCardsIn(ZoneType.Exile).stream().anyMatch(c->c.getName().equals("Ragavan, Nimble Pilferer")),"Whip replaces destruction destination with exile");Assert.assertFalse(ai.getCardsIn(ZoneType.Graveyard).stream().anyMatch(c->c.getName().equals("Ragavan, Nimble Pilferer")));Assert.assertEquals(opp.getLandsInPlay().stream().filter(Card::isTapped).count(),2L);
  groups++;System.out.println("PACKAGE Whip paid4cast+4activate destroyedBodyExiled=true");
 }
 public static void main(String[]args){var t=new PackageRecoveryRegression();t.initializeModel();t.victimize();t.whipExile();System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
