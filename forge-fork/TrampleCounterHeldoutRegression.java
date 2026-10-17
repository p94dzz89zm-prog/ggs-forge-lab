import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.Keyword;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Fresh frozen constructed trample rescue; not natural games. */
public class TrampleCounterHeldoutRegression extends TrampleCounterRescueRegression {
 void heldout(int life,String counterName,String targetName,String shieldName,boolean mixedDefender,boolean baselineBuild) {
  String profile="BALANCED";
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);System.clearProperty("dragonmind.disableCounterRescuePolicy");
  for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(life,null);
  Card target=addCard(targetName,enemy),other=addCard("Raging Goblin",enemy),shield=addCard(shieldName,ai);
  for(Card body:List.of(target,other,shield)){body.setSickness(false);body.setTurnInZone(-1);}
  Card counterCard=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);combat.addAttacker(target,ai);combat.addAttacker(other,ai);if(mixedDefender){Card extra=addCard("Raging Goblin",enemy);extra.setSickness(false);combat.addAttacker(extra,remover);combat.setBlocked(extra,false);}combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(removal.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  int spill=Math.max(0,target.getNetCombatDamage()-shield.getNetToughness());Assert.assertTrue(spill+other.getNetCombatDamage()>=life && other.getNetCombatDamage()<life,"declared fresh fixture is lethal before removal, survivable after");
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  if(!baselineBuild)Assert.assertNull(choice,"conserve saving removal in actual priority");
  boolean countered=choice!=null;
  if(countered){Assert.assertEquals(choice.size(),1);var cast=choice.get(0);Assert.assertEquals(cast.getHostCard(),counterCard);Assert.assertTrue(cast.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(cast,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),countered);Assert.assertEquals(counterCard.isInZone(ZoneType.Hand),!countered);Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),countered?(counterName.equals("Counterspell")?2L:1L):0L);
  Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(body->body.isToken()&&body.getName().contains("Treasure")).count(),countered&&counterName.equals("An Offer You Can't Refuse")?2L:0L);
  combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);Assert.assertEquals(ai.getLife(),life-other.getNetCombatDamage()-(countered?spill:0),"actual declared blockers and trample damage");if(!baselineBuild)Assert.assertTrue(ai.getLife()>0);
  System.out.println("HELDOUT_TRAMPLE profile="+profile+" life="+life+" card="+counterName+" mixed="+mixedDefender+" countered="+countered+" after="+ai.getLife());groups++;
 }
 public static void main(String[]args){if(args.length<2||!args[0].equals("--purpose")||!args[1].equals("heldout"))throw new IllegalArgumentException("Requires --purpose heldout");TrampleCounterHeldoutRegression t=new TrampleCounterHeldoutRegression();t.initializeModel();boolean baseline=Arrays.asList(args).contains("--baseline");t.heldout(2,"Swan Song","Stampeding Rhino","Grizzly Bears",false,baseline);t.heldout(5,"Swan Song","Charging Monstrosaur","Memnite",true,baseline);t.heldout(3,"An Offer You Can't Refuse","Charging Monstrosaur","Runeclaw Bear",false,baseline);t.heldout(5,"An Offer You Can't Refuse","Colossal Dreadmaw","Grizzly Bears",true,baseline);t.heldout(4,"Counterspell","Stampeding Rhino","Memnite",true,baseline);t.heldout(4,"Counterspell","Colossal Dreadmaw","Runeclaw Bear",false,baseline);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
