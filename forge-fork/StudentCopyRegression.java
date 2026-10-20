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

/** Actual pump/ninjutsu/copy/damage; constructed mechanisms, not natural games. */
public class StudentCopyRegression extends CounterRescuePaymentRegression {
 boolean baseline;int groups;
 void scenario(String profile,String bodyName,String pumpName,int life,boolean badSwap) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile",profile);
  for(Player p:g.getPlayers())fillLibrary(p,20);opp.setLife(life,null);
  Card outgoing=addCard(badSwap?"Dauthi Voidwalker":"Memnite",ai),template=addCard(bodyName,opp);
  outgoing.setSickness(false);outgoing.setTurnInZone(-1);template.setSickness(false);template.setTurnInZone(-1);
  int copiedPower=template.getNetCombatDamage();addCard("Island",ai);addCard("Island",ai);
  Card student=addCardToZone("Sakashima's Student",ai,ZoneType.Hand);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);
  if(pumpName!=null){
   int cost=pumpName.equals("Might of Oaks")?4:1;for(int i=0;i<cost;i++)addCard("Forest",opp);
   SpellAbility pump=addCardToZone(pumpName,opp,ZoneType.Hand).getFirstSpellAbility();pump.setActivatingPlayer(opp);pump.getTargets().add(template);
   Assert.assertTrue(pump.canPlay());Assert.assertTrue(pump.canTarget(template));Assert.assertTrue(ComputerUtilCost.canPayCost(pump,opp,false));
   Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(opp,pump,null));drain(g);
   Assert.assertEquals(opp.getLandsInPlay().stream().filter(Card::isTapped).count(),(long)cost);
   Assert.assertEquals(template.getNetCombatDamage(),copiedPower+(pumpName.equals("Might of Oaks")?7:3));
  }
  Combat combat=new Combat(ai);combat.addAttacker(outgoing,opp);combat.setBlocked(outgoing,false);
  g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,ai,false);
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertNull(CombatUtil.validateBlocks(combat,opp));
  SpellAbility sa=ComputerUtilAbility.getSpellAbilities(new CardCollection(student),ai).stream().filter(SpellAbility::isNinjutsu).findFirst().orElseThrow();sa.setActivatingPlayer(ai);
  int battlefieldCount=g.getCardsIn(ZoneType.Battlefield).size();
  var plan=GgsNinjutsuPolicy.choose(ai,sa,combat.getUnblockedAttackers());Assert.assertNotNull(plan);
  boolean willing=((PlayerControllerAi)ai.getController()).getAi().canPlaySa(sa).willingToPlay();
  Assert.assertEquals(g.getCardsIn(ZoneType.Battlefield).size(),battlefieldCount,"forecast must not add a live creature");
  Assert.assertEquals(willing,!badSwap||baseline,"automatic clone choice "+profile+" "+bodyName);
  if(willing){
   Assert.assertTrue(sa.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(sa,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));drain(g);
   Assert.assertTrue(outgoing.isInZone(ZoneType.Hand));Assert.assertTrue(combat.isAttacking(student));
   Assert.assertEquals(student.getName(),bodyName);Assert.assertEquals(student.getNetCombatDamage(),copiedPower,"pump is not copied");
  }else{
   Assert.assertTrue(student.isInZone(ZoneType.Hand));Assert.assertTrue(combat.isAttacking(outgoing));Assert.assertTrue(g.getStack().isEmpty());
  }
  Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),willing?2L:0L);
  combat.assignCombatDamage(false);combat.dealAssignedDamage();g.getAction().checkStateEffects(true);
  Assert.assertEquals(opp.getLife(),life-(willing?copiedPower:3));
  groups++;System.out.println("STUDENT_COPY profile="+profile+" body="+bodyName+" pump="+pumpName+" badSwap="+badSwap+" willing="+willing+" finalLife="+opp.getLife()+" forecast="+plan.reason());
 }
 public static void main(String[] args){
  var t=new StudentCopyRegression();t.initializeModel();t.baseline=Arrays.asList(args).contains("--baseline");
  if(Arrays.asList(args).contains("--heldout")){
   for(String body:List.of("Runeclaw Bear","Ashcoat Bear"))for(int life:List.of(4,5))t.scenario("BALANCED",body,"Might of Oaks",life,true);
   for(int life:List.of(2,3))t.scenario("BALANCED","Hill Giant",null,life,false);
  }else for(String profile:List.of("BALANCED","ENGINE","ECONOMY")){
   t.scenario(profile,"Grizzly Bears","Giant Growth",4,true);t.scenario(profile,"Grizzly Bears",null,2,false);
  }
  System.out.println("Checks passed: "+t.groups);System.exit(0);
 }
}
