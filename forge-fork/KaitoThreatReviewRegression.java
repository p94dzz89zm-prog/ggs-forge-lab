import forge.ai.*;
import forge.game.*;
import forge.game.ability.ApiType;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;

/** Reduced constructed follow-up to cycle16 turn49, not an exact game replay.
 * Base-power Combustion Man and six life replace observed buffed five power
 * and seven life; both have lethal after the visible Sword equip.
 */
public class KaitoThreatReviewRegression extends PackageRecoveryRegression {
 void review(boolean defend){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(6,null);opp.setLifeLostThisTurn(9);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");System.setProperty("dragonmind.linePlanner","false");
  Card threat=addCard("Combustion Man",opp),regalia=addCard("Brotherhood Regalia",opp),sword=addCard("Vorpal Sword",opp);threat.setSickness(false);threat.setTurnInZone(-1);
  addCard("Goro-Goro and Satoru",ai);addCard("Shivan Dragon",ai);
  addCard("Island",ai);addCard("Island",ai);addCard("Swamp",ai);addCard("Swamp",ai);for(int i=0;i<5;i++)addCard("Swamp",opp);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN2,ai,false);g.getAction().checkStateEffects(true);Card kaito=cast(ai,addCardToZone("Kaito, Bane of Nightmares",ai,ZoneType.Hand));
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(choices);Assert.assertFalse(choices.isEmpty());SpellAbility chosen=choices.get(0);System.out.println("KAITO stockChoice="+chosen.getApi()+" host="+chosen.getHostCard().getName());
  Assert.assertEquals(chosen.getHostCard(),kaito);Assert.assertEquals(chosen.getApi(),ApiType.Surveil,"reproduce draw preference with visible unequipped threat package");
  SpellAbility action=defend?kaito.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Tap).findFirst().orElseThrow():chosen;action.setActivatingPlayer(ai);
  if(defend){Assert.assertTrue(action.canTarget(threat));action.getTargets().add(threat);}play(ai,action);
  if(defend){Assert.assertTrue(threat.isTapped());Assert.assertEquals(threat.getCounters(CounterEnumType.STUN),2);}
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,opp,false);
  for(Card equipment:new Card[]{regalia,sword}){SpellAbility equip=equipment.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Attach).findFirst().orElseThrow();equip.setActivatingPlayer(opp);Assert.assertTrue(equip.canTarget(threat));equip.getTargets().add(threat);play(opp,equip);}
  Assert.assertEquals(threat.getNetPower(),6);
  if(defend){Assert.assertFalse(CombatUtil.canAttack(threat,ai));Assert.assertEquals(ai.getLife(),6);}
  else{Assert.assertTrue(CombatUtil.canAttack(threat,ai));Combat combat=new Combat(opp);combat.addAttacker(threat,ai);combat.setBlocked(threat,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));for(Card blocker:ai.getCreaturesInPlay())Assert.assertFalse(CombatUtil.canBlock(threat,blocker));combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(ai.getLife(),0);}
  groups++;System.out.println("KAITO defensiveAlternative="+defend+" afterVisibleEquipThreat life="+ai.getLife());
 }
 public static void main(String[]args){var t=new KaitoThreatReviewRegression();t.initializeModel();t.review(false);t.review(true);System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
