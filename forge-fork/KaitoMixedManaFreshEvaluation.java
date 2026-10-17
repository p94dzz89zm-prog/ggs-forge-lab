import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Separate frozen constructed equipment lines; no whole-game/strength claim. */
public class KaitoMixedManaFreshEvaluation extends PackageRecoveryRegression {
 void scenario(String creature,int life,List<String> mana,boolean lethal,boolean candidate){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(2);for(Player p:g.getPlayers())fillLibrary(p,40);ai.setLife(life,null);opp.setLifeLostThisTurn(9);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");System.setProperty("dragonmind.strategyProfile","BALANCED");
  Card threat=addCard(creature,opp),regalia=addCard("Brotherhood Regalia",opp),sword=addCard("Vorpal Sword",opp);threat.setSickness(false);threat.setTurnInZone(-1);
  addCard("Goro-Goro and Satoru",ai);addCard("Shivan Dragon",ai);for(String n:List.of("Island","Island","Swamp","Swamp"))addCard(n,ai);for(String n:mana)addCard(n,opp).setTapped(true);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN2,ai,false);g.getAction().checkStateEffects(true);Card kaito=cast(ai,addCardToZone("Kaito, Bane of Nightmares",ai,ZoneType.Hand));
  String before=PlannerSnapshot.forPlayer(ai).toString();var rng=forge.util.MyRandom.getRandom();var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);SpellAbility action=choices.get(0);
  boolean defend=candidate&&lethal;Assert.assertEquals(action.getHostCard(),kaito);Assert.assertEquals(action.getApi(),defend?ApiType.Tap:ApiType.Surveil,creature+" life="+life+" mana="+mana);
  Assert.assertEquals(PlannerSnapshot.forPlayer(ai).toString(),before,"selection must preserve live position");Assert.assertSame(forge.util.MyRandom.getRandom(),rng,"forecast restores RNG object");
  if(defend)Assert.assertEquals(action.getTargetCard(),threat);play(ai,action);
  if(lethal){
   if(defend){Assert.assertEquals(threat.getCounters(CounterEnumType.STUN),2);Assert.assertEquals(kaito.getCounters(CounterEnumType.LOYALTY),2);}
   g.getPhaseHandler().devModeSet(PhaseType.UNTAP,opp,false);for(Card land:opp.getLandsInPlay())land.untap(opp);if(threat.isTapped())threat.untap(opp);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,opp,false);
   for(Card eq:List.of(sword,regalia)){SpellAbility equip=eq.getSpellAbilities().stream().peek(sa->sa.setActivatingPlayer(opp)).filter(sa->sa.getApi()==ApiType.Attach&&sa.canTarget(threat)).min(Comparator.comparingInt(sa->sa.getPayCosts().getTotalMana().getCMC())).orElseThrow();equip.getTargets().add(threat);play(opp,equip);Assert.assertEquals(eq.getEquipping(),threat);}
   Assert.assertEquals(opp.getLandsInPlay().stream().filter(Card::isTapped).count(),threat.getType().isLegendary()?3L:5L,"combined actual payment");
   if(defend){Assert.assertFalse(CombatUtil.canAttack(threat,ai));Assert.assertEquals(threat.getCounters(CounterEnumType.STUN),1);Assert.assertEquals(ai.getLife(),life);}
   else{Assert.assertTrue(CombatUtil.canAttack(threat,ai));for(Card c:ai.getCreaturesInPlay())Assert.assertFalse(CombatUtil.canBlock(threat,c));Combat combat=new Combat(opp);combat.addAttacker(threat,ai);combat.setBlocked(threat,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertTrue(ai.getLife()<=0);}
  }
  groups++;System.out.println("FRESH creature="+creature+" life="+life+" defend="+defend+" after="+ai.getLife());
 }
 public static void main(String[]args){boolean candidate=Boolean.parseBoolean(args[0]);var t=new KaitoMixedManaFreshEvaluation();t.initializeModel();
  t.scenario("Dragonlord Kolaghan",8,List.of("Blood Crypt","Watery Grave","Island"),true,candidate);
  t.scenario("Nicol Bolas, the Ravager",6,List.of("Blood Crypt","Underground Sea","Mountain"),true,candidate);
  t.scenario("Doom Whisperer",8,List.of("Badlands","Swamp","Island","Mountain","Plains"),true,candidate);
  t.scenario("Dragonlord Kolaghan",8,List.of("Blood Crypt","Island","Island"),false,candidate);
  t.scenario("Doom Whisperer",8,List.of("Badlands","Swamp","Island","Mountain"),false,candidate);
  t.scenario("Slippery Bogle",3,List.of("Badlands","Swamp","Island","Mountain","Plains"),false,candidate);
  t.scenario("Doom Whisperer",9,List.of("Badlands","Swamp","Island","Mountain","Plains"),false,candidate);
  System.out.println("Checks passed: "+t.groups);System.exit(0);
 }
}
