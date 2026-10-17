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

/** Constructed actual-priority/payment/combat checks; not natural games. */
public class CombinedCounterRescueHeldoutRegression extends CounterRescuePaymentRegression {
 int groups;
 void combined(String profile,int life,String targetName,String otherName,boolean baselineBuild) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);System.clearProperty("dragonmind.disableCounterRescuePolicy");
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(life,null);
  Card target=addCard(targetName,enemy),other=addCard(otherName,enemy);
  for(Card c:List.of(target,other)){c.setSickness(false);c.setTurnInZone(-1);}
  Card swan=addCardToZone("Swan Song",ai,ZoneType.Hand),blue=addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);for(Card c:List.of(target,other)){combat.addAttacker(c,ai);combat.setBlocked(c,false);}
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(removal.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  boolean baseline=choice!=null;boolean rescuing=target.getNetCombatDamage()+other.getNetCombatDamage()>=life && other.getNetCombatDamage()<life; if(!baselineBuild && rescuing)Assert.assertNull(choice,"corrected priority declines lethal rescue counter");
  if(choice!=null){Assert.assertEquals(choice.size(),1);SpellAbility counter=choice.get(0);Assert.assertEquals(counter.getHostCard(),swan);Assert.assertTrue(counter.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(counter,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,counter,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),baseline);Assert.assertEquals(blue.isTapped(),baseline);Assert.assertEquals(swan.isInZone(ZoneType.Hand),!baseline);
  int damage=other.getNetCombatDamage()+(baseline?target.getNetCombatDamage():0);combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(ai.getLife(),life-damage);
  if(!baselineBuild && rescuing)Assert.assertTrue(ai.getLife()>0,"actual surviving result after saving removal");System.out.println("HELDOUT_COMBINED target="+targetName+" profile="+profile+" life="+life+" other="+otherName+" rescuing="+rescuing+" baseline="+baseline+" after="+ai.getLife());groups++;
 }
 public static void main(String[]args){if(args.length<2||!args[0].equals("--purpose")||!args[1].equals("heldout"))throw new IllegalArgumentException("Requires --purpose heldout");boolean baseline=Arrays.asList(args).contains("--baseline");CombinedCounterRescueHeldoutRegression t=new CombinedCounterRescueHeldoutRegression();t.initializeModel();t.combined("BALANCED",5,"Hill Giant","Grizzly Bears",baseline);t.combined("BALANCED",6,"Hill Giant","Grizzly Bears",baseline);t.combined("BALANCED",6,"Centaur Courser","Hill Giant",baseline);t.combined("BALANCED",7,"Centaur Courser","Hill Giant",baseline);t.combined("BALANCED",3,"Grizzly Bears","Elvish Warrior",baseline);t.combined("BALANCED",4,"Grizzly Bears","Elvish Warrior",baseline);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
