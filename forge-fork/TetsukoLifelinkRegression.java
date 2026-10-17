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

/** Constructed package interactions, not whole-deck outcome comparisons. */
public class TetsukoLifelinkRegression extends CounterRescuePaymentRegression {
 int groups;
 Card cast(Player ai,Card card){SpellAbility sa=card.getFirstSpellAbility();sa.setActivatingPlayer(ai);Assert.assertTrue(sa.canPlay(),"actual cast legality "+card.getName());Assert.assertTrue(ComputerUtilCost.canPayCost(sa,ai,false),"actual mana "+card.getName());Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null),"actual payment "+card.getName());drain(ai.getGame());return ai.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getId()==card.getId()).findFirst().orElseThrow(()->new AssertionError("Permanent failed to resolve: "+card.getName()+" board="+ai.getCardsIn(ZoneType.Battlefield)+" stack="+ai.getGame().getStack()));}
 void equipment(String name){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);
  Card access=addCard("Tetsuko Umezawa, Fugitive",ai),carrier=addCard(name,ai),blocker=addCard("Grizzly Bears",opp);access.setTurnInZone(-1);carrier.setTurnInZone(-1);carrier.setSickness(false);
  for(int i=0;i<3;i++)addCard("Swamp",ai);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  Assert.assertFalse(CombatUtil.canBlock(carrier,blocker),"Tetsuko access before equipment");
  Card spear=cast(ai,addCardToZone("Shadowspear",ai,ZoneType.Hand));
  SpellAbility equip=spear.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Attach).findFirst().orElseThrow();equip.setActivatingPlayer(ai);equip.getTargets().add(carrier);
  Assert.assertTrue(equip.canPlay());Assert.assertTrue(equip.canTarget(carrier));Assert.assertTrue(ComputerUtilCost.canPayCost(equip,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,equip,null));drain(g);
  Assert.assertTrue(carrier.getNetPower()>1&&carrier.getNetToughness()>1);
  Assert.assertTrue(CombatUtil.canBlock(carrier,blocker),"Tetsuko threshold lost after +1/+1; menace grouping is separate");
  Assert.assertTrue(carrier.hasKeyword(Keyword.LIFELINK));Assert.assertTrue(carrier.hasKeyword(Keyword.TRAMPLE));
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  groups++;System.out.println("PACKAGE Shadowspear carrier="+name+" paid3 thresholdLost=true");
 }
 void whip(boolean twoAttackers){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);
  Card commander=addCard("Goro-Goro and Satoru",ai),access=addCard("Tetsuko Umezawa, Fugitive",ai),blocker=addCard("Grizzly Bears",opp);commander.setTurnInZone(-1);access.setTurnInZone(-1);commander.setCommander(true);
  for(int i=0;i<(twoAttackers?5:4);i++)addCard("Swamp",ai);for(int i=0;i<3;i++)addCard("Mountain",ai);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);
  Card whip=cast(ai,addCardToZone("Whip of Erebos",ai,ZoneType.Hand));
  Card ragavan=cast(ai,addCardToZone("Ragavan, Nimble Pilferer",ai,ZoneType.Hand));Card extra=twoAttackers?cast(ai,addCardToZone("Gingerbrute",ai,ZoneType.Hand)):null;
  SpellAbility haste=commander.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.PumpAll).findFirst().orElseThrow();haste.setActivatingPlayer(ai);Assert.assertTrue(haste.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(haste,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,haste,null));drain(g);
  Assert.assertEquals(ragavan.getNetPower(),2);Assert.assertEquals(ragavan.getNetToughness(),1);Assert.assertTrue(ragavan.enteredThisTurn());Assert.assertTrue(ragavan.hasKeyword(Keyword.LIFELINK));Assert.assertTrue(ragavan.hasKeyword(Keyword.HASTE));Assert.assertFalse(CombatUtil.canBlock(ragavan,blocker));
  Combat combat=new Combat(ai);combat.addAttacker(ragavan,opp);combat.setBlocked(ragavan,false);if(extra!=null){combat.addAttacker(extra,opp);combat.setBlocked(extra,false);}
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,opp));
  int damage=twoAttackers?3:2;combat.assignCombatDamage(false);combat.dealAssignedDamage();drain(g);
  Assert.assertEquals(ai.getLife(),20+damage);Assert.assertEquals(opp.getLife(),20-damage);
  var dragons=ai.getCreaturesInPlay().stream().filter(c->c.isToken()&&c.getName().contains("Dragon Spirit")).toList();Assert.assertEquals(dragons.size(),1,"one qualifying damage event, not one Dragon per attacker");
  Assert.assertFalse(dragons.get(0).hasKeyword(Keyword.HASTE),"GGS haste applied before this Dragon entered");Assert.assertTrue(dragons.get(0).hasKeyword(Keyword.LIFELINK));
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),twoAttackers?8L:7L);
  groups++;System.out.println("PACKAGE Whip attackers="+(twoAttackers?2:1)+" damage="+damage+" lifeGain="+damage+" dragons=1 newDragonHaste=false");
 }
 public static void main(String[]args){var t=new TetsukoLifelinkRegression();t.initializeModel();t.equipment("Ragavan, Nimble Pilferer");t.equipment("Kari Zev, Skyship Raider");t.whip(false);t.whip(true);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
