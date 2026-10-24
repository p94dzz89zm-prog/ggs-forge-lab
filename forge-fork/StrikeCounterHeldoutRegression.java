import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.keyword.Keyword;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;
/** Diagnostic constructed boundary; not a heldout strength evaluation. */
public class StrikeCounterHeldoutRegression extends CounterRescuePaymentRegression {
 int groups;
 void scenario(String counterName,int mode,boolean baseline,int variant) {
  boolean manualPass=false;
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");
  for(Player p:g.getPlayers())fillLibrary(p,20);int life=0;
  Card target=addCard(variant==0?"Stampeding Rhino":"Charging Monstrosaur",enemy),other=addCard(variant==0?"Grizzly Bears":"Raging Goblin",enemy),shield=addCard(mode==2?"White Knight":"Memnite",ai);
  for(Card body:List.of(target,other,shield)){body.setSickness(false);body.setTurnInZone(-1);}
  if(mode<2)addCard(mode==0?"Chariot of Victory":"Fireshrieker",enemy).attachToEntity(target,null);g.getAction().checkStateEffects(true);
  Assert.assertTrue(mode==2?shield.hasKeyword(Keyword.FIRST_STRIKE):target.hasKeyword(mode==0?Keyword.FIRST_STRIKE:Keyword.DOUBLE_STRIKE));
  int spill=target.getNetCombatDamage()-shield.getLethalDamage();life=spill*(mode==1?2:1)+other.getNetCombatDamage();Assert.assertTrue(spill>0);ai.setLife(life,null);
  Card counter=addCardToZone(counterName,ai,ZoneType.Hand);addCard("Island",ai);if(counterName.equals("Counterspell"))addCard("Island",ai);
  for(String land:List.of("Plains","Swamp","Swamp"))addCard(land,remover);
  Combat combat=new Combat(enemy);combat.addAttacker(target,ai);combat.addAttacker(other,ai);combat.addBlocker(target,shield);combat.setBlocked(target,true);combat.setBlocked(other,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,enemy,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,ai));combat.orderBlockersForDamageAssignment();combat.orderAttackersForDamageAssignment();
  var removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canPlay());Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  var choice=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();boolean countered=!manualPass&&choice!=null;
  Assert.assertEquals(choice!=null,baseline,"frozen automatic rescue decision");
  if(countered){var cast=choice.get(0);Assert.assertEquals(cast.getHostCard(),counter);Assert.assertTrue(cast.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(cast,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,cast,null));}
  drain(g);Assert.assertEquals(target.isInZone(ZoneType.Battlefield),countered);
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),countered?(counterName.equals("Counterspell")?2L:1L):0L);
  Assert.assertEquals(remover.getCardsIn(ZoneType.Battlefield).stream().filter(b->b.isToken()&&b.getName().contains("Treasure")).count(),countered&&counterName.equals("An Offer You Can't Refuse")?2L:0L);
  combat.assignCombatDamage(true);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);drain(g);
  if(ai.getLife()>0){combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);}
  Assert.assertEquals(ai.getLife(),countered?(mode==1?-1:0):life-other.getNetCombatDamage());Assert.assertEquals(ai.getLife()>0,!baseline);groups++;
  System.out.println("HELDOUT_STRIKE variant="+variant+" mode="+mode+" card="+counterName+" manualPass="+manualPass+" automaticChoice="+(choice!=null)+" countered="+countered+" finalLife="+ai.getLife());
 }
 public static void main(String[]args){Assert.assertTrue(Arrays.asList(args).contains("--purpose")&&Arrays.asList(args).contains("heldout"));StrikeCounterHeldoutRegression t=new StrikeCounterHeldoutRegression();t.initializeModel();boolean baseline=Arrays.asList(args).contains("--baseline");String[]cards={"Swan Song","An Offer You Can't Refuse","Counterspell"};for(int variant=0;variant<2;variant++)for(int mode=0;mode<3;mode++)t.scenario(cards[(variant+mode)%3],mode,baseline,variant);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}

