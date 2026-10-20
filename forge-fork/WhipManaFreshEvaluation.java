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

/** Frozen separate constructed payment cases, not natural games. */
public class WhipManaFreshEvaluation extends PackageRecoveryRegression {
 void scenario(String body,int black,List<String> other,boolean recoverable,boolean candidate){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(2);for(Player p:g.getPlayers())fillLibrary(p,30);ai.setLife(7,null);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  for(int i=0;i<black;i++)addCard("Swamp",ai);for(String n:other)addCard(n,ai);addCard("Goro-Goro and Satoru",ai);addToken("r_5_5_dragon_spirit_flying",ai);
  Card whip=addCardToZone("Whip of Erebos",ai,ZoneType.Hand),grave=body==null?null:addCardToZone(body,ai,ZoneType.Graveyard);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);g.getAction().checkStateEffects(true);var controller=((PlayerControllerAi)ai.getController()).getAi();String before=PlannerSnapshot.forPlayer(ai).toString();var choices=controller.chooseSpellAbilityToPlay();
  Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);Assert.assertEquals(choices.get(0).getHostCard(),whip);Assert.assertEquals(PlannerSnapshot.forPlayer(ai).toString(),before,"reservation must not mutate live cards/hand/mana");
  var remembered=AiCardMemory.getMemorySet(ai,AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);Assert.assertEquals(remembered.size(),candidate&&recoverable?2:0,"reserve only after a payable combined line");
  play(ai,choices.get(0));var next=controller.chooseSpellAbilityToPlay();Assert.assertTrue(controller.getCardMemory().isMemorySetEmpty(AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL),"one-spell reservation clears on next decision");
  if(grave!=null){Card resolved=ai.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getName().equals("Whip of Erebos")).findFirst().orElseThrow();SpellAbility rise=resolved.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElseThrow();rise.setActivatingPlayer(ai);rise.getTargets().add(grave);
   boolean payable=candidate&&recoverable;Assert.assertEquals(ComputerUtilCost.canPayCost(rise,ai,false),payable);
   if(payable){Assert.assertNotNull(next);Assert.assertEquals(next.size(),1);Assert.assertEquals(next.get(0).getApi(),ApiType.ChangeZone,"real next controller selects recovery");play(ai,next.get(0));Card returned=permanent(ai,body);Assert.assertTrue(returned.hasKeyword(forge.game.keyword.Keyword.HASTE));Assert.assertTrue(returned.hasKeyword(forge.game.keyword.Keyword.LIFELINK));Assert.assertTrue(CombatUtil.canAttack(returned,opp));Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),8L);
    Combat combat=new Combat(ai);combat.addAttacker(returned,opp);combat.setBlocked(returned,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));int power=returned.getNetPower();combat.assignCombatDamage(false);combat.dealAssignedDamage();drain(g);Assert.assertEquals(ai.getLife(),7+power);Assert.assertEquals(opp.getLife(),20-power);
   }
  }
  groups++;System.out.println("WHIP_FRESH body="+body+" black="+black+" total="+(black+other.size())+" candidate="+candidate+" recovered="+(candidate&&recoverable));
 }
 public static void main(String[]args){var t=new WhipManaFreshEvaluation();t.initializeModel();boolean c=Boolean.parseBoolean(args[0]);
  t.scenario("Loyal Apprentice",4,List.of("Island","Island","Mountain","Mountain"),true,c);
  t.scenario("Phoenix Chick",4,List.of("Mountain","Mountain","Mountain","Island"),true,c);
  t.scenario("Hope of Ghirapur",4,List.of("Island","Island","Island","Island"),true,c);
  t.scenario(null,4,List.of("Island","Island","Mountain","Mountain"),false,c);
  t.scenario("Loyal Apprentice",4,List.of("Island","Island","Mountain"),false,c);
  t.scenario("Phoenix Chick",2,List.of("Island","Island","Island","Mountain","Mountain","Mountain"),false,c);
  System.out.println("Checks passed: "+t.groups);System.exit(0);
 }
}
