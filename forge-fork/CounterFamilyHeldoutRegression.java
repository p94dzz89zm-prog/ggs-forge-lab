import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Frozen fresh constructed counter-family comparisons, not natural games. */
public class CounterFamilyHeldoutRegression extends CounterFamilyRegression {
 void heldout(String profile,int life,String targetName,String otherName,boolean baselineBuild) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);System.clearProperty("dragonmind.disableCounterRescuePolicy");
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(life,null);
  Card target=addCard(targetName,enemy),other=addCard(otherName,enemy);
  for(Card c:List.of(target,other)){c.setSickness(false);c.setTurnInZone(-1);}
  Card swan=addCardToZone(counterName,ai,ZoneType.Hand),blue=addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);for(Card c:List.of(target,other)){combat.addAttacker(c,ai);combat.setBlocked(c,false);}
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(removal.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  boolean baseline=choice!=null;if(!baselineBuild)Assert.assertNull(choice,"corrected priority conserves saving removal");
  if(choice!=null){Assert.assertEquals(choice.size(),1);SpellAbility counter=choice.get(0);Assert.assertEquals(counter.getHostCard(),swan);Assert.assertTrue(counter.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(counter,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,counter,null));}
  drain(g);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),baseline?(counterName.equals("Counterspell")?2L:1L):0L,"actual colored counter payment");Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.isToken()&&c.getName().contains("Treasure")).count(),baseline&&counterName.equals("An Offer You Can't Refuse")?2L:0L,"actual Offer resolution creates two Treasures");Assert.assertEquals(target.isInZone(ZoneType.Battlefield),baseline);Assert.assertEquals(blue.isTapped(),baseline);Assert.assertEquals(swan.isInZone(ZoneType.Hand),!baseline);
  int damage=other.getNetCombatDamage()+(baseline?target.getNetCombatDamage():0);combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(ai.getLife(),life-damage);
  Assert.assertEquals(ai.getLife()>0,!baseline);System.out.println("HELDOUT_FAMILY target="+targetName+" card="+counterName+" profile="+profile+" life="+life+" other="+otherName+" baseline="+baseline+" after="+ai.getLife());groups++;
 }
 public static void main(String[]args){if(args.length<2||!args[0].equals("--purpose")||!args[1].equals("heldout"))throw new IllegalArgumentException("Requires --purpose heldout");CounterFamilyHeldoutRegression t=new CounterFamilyHeldoutRegression();t.initializeModel();boolean baseline=Arrays.asList(args).contains("--baseline");t.counterName="An Offer You Can't Refuse";t.heldout("BALANCED",6,"Air Elemental","Grizzly Bears",baseline);t.heldout("BALANCED",5,"Serra Angel","Elvish Warrior",baseline);t.heldout("BALANCED",4,"Air Elemental","Eager Cadet",baseline);t.counterName="Counterspell";t.heldout("BALANCED",6,"Air Elemental","Grizzly Bears",baseline);t.heldout("BALANCED",6,"Hill Giant","Hill Giant",baseline);t.heldout("BALANCED",4,"Serra Angel","Eager Cadet",baseline);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
