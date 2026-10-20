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

/** Frozen separate constructed conditions; no natural-game strength estimate. */
public class KaitoThreatEvaluation extends PackageRecoveryRegression {
 void scenario(String creature,int life,int swamps,boolean tapped,boolean main1,boolean hasSword,boolean lethal,boolean candidate){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);for(Player p:g.getPlayers())fillLibrary(p,20);ai.setLife(life,null);opp.setLifeLostThisTurn(9);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");
  Card threat=addCard(creature,opp),regalia=addCard("Brotherhood Regalia",opp),sword=hasSword?addCard("Vorpal Sword",opp):null;threat.setSickness(false);threat.setTurnInZone(-1);threat.setTapped(tapped);
  addCard("Goro-Goro and Satoru",ai);addCard("Shivan Dragon",ai);addCard("Island",ai);addCard("Island",ai);addCard("Swamp",ai);addCard("Swamp",ai);for(int i=0;i<swamps;i++)addCard("Swamp",opp);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN2,ai,false);g.getAction().checkStateEffects(true);Card kaito=cast(ai,addCardToZone("Kaito, Bane of Nightmares",ai,ZoneType.Hand));if(main1)g.getPhaseHandler().devModeSet(PhaseType.MAIN1,ai,false);
  if(creature.startsWith("Tel-Jilad")){
   for(Card equipment:new Card[]{regalia,sword})for(SpellAbility equip:equipment.getSpellAbilities())if(equip.getApi()==ApiType.Attach){equip.setActivatingPlayer(opp);Assert.assertFalse(equip.canTarget(threat),"protection from artifacts prevents the forecast equipment target");}
   SpellAbility tap=kaito.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Tap).findFirst().orElseThrow();tap.setActivatingPlayer(ai);Assert.assertTrue(tap.canTarget(threat),"Kaito remains a legal target source; distinguish these two restrictions");
  }
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  if(main1){
   // Stock MAIN1 willingness is stochastic and earlier alternate actions
   // consume RNG differently. Test the actual guard's no-override contract
   // on an identical supplied legal draw choice, not a false RNG assumption.
   SpellAbility draw=kaito.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Surveil).findFirst().orElseThrow();draw.setActivatingPlayer(ai);Assert.assertTrue(draw.canPlay());var stock=java.util.List.of(draw);
   if(candidate)try{Object result=Class.forName("forge.ai.ggs.GgsKaitoThreatPolicy").getMethod("select",Player.class,java.util.List.class).invoke(null,ai,stock);Assert.assertSame(result,stock,"MAIN1 preserves supplied stock decision");}catch(ReflectiveOperationException e){throw new AssertionError(e);}
   groups++;System.out.println("EVALUATION MAIN1 identicalStockDecisionPreserved=true candidate="+candidate);return;
  }
  Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);SpellAbility action=choices.get(0);Assert.assertEquals(action.getHostCard(),kaito);
  boolean defended=candidate&&lethal;Assert.assertEquals(action.getApi(),defended?ApiType.Tap:ApiType.Surveil,"choice scope "+creature+" life="+life+" swamps="+swamps);
  if(defended)Assert.assertEquals(action.getTargetCard(),threat);play(ai,action);
  if(lethal){
   if(defended){Assert.assertTrue(threat.isTapped());Assert.assertEquals(threat.getCounters(CounterEnumType.STUN),2);Assert.assertEquals(kaito.getCounters(CounterEnumType.LOYALTY),2);}
   g.getPhaseHandler().devModeSet(PhaseType.MAIN1,opp,false);
   for(Card equipment:new Card[]{regalia,sword}){SpellAbility equip=equipment.getSpellAbilities().stream().filter(sa->{sa.setActivatingPlayer(opp);return sa.getApi()==ApiType.Attach&&sa.canTarget(threat);}).findFirst().orElseThrow();Assert.assertTrue(equip.canTarget(threat));equip.getTargets().add(threat);play(opp,equip);}
   if(defended){Assert.assertFalse(CombatUtil.canAttack(threat,ai));Assert.assertEquals(ai.getLife(),life);}
   else{Assert.assertTrue(CombatUtil.canAttack(threat,ai));Combat combat=new Combat(opp);combat.addAttacker(threat,ai);combat.setBlocked(threat,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,opp,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));for(Card blocker:ai.getCreaturesInPlay())Assert.assertFalse(CombatUtil.canBlock(threat,blocker));combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertTrue(ai.getLife()<=0);}
  }
  groups++;System.out.println("EVALUATION creature="+creature+" life="+life+" swamps="+swamps+" candidate="+candidate+" defend="+defended+" after="+ai.getLife());
 }
 public static void main(String[]args){boolean candidate=Boolean.parseBoolean(args[0]);var t=new KaitoThreatEvaluation();t.initializeModel();String mode=args.length>1?args[1]:"initial";
  if(mode.equals("targetability")){t.scenario("White Knight",4,5,false,false,true,false,candidate);}
  else if(mode.equals("artifact-targetability")){t.scenario("Tel-Jilad Chosen",4,5,false,false,true,false,candidate);}
  else if(mode.equals("fresh")){t.scenario("Glorybringer",5,5,false,false,true,true,candidate);t.scenario("Bloodbraid Marauder",5,5,false,false,true,true,candidate);t.scenario("Thraximundar",8,3,false,false,true,true,candidate);t.scenario("Tel-Jilad Archers",4,5,false,false,true,false,candidate);t.scenario("Silver Knight",5,5,false,false,true,false,candidate);t.scenario("Silver Knight",4,4,false,false,true,false,candidate);t.scenario("Glorybringer",5,5,true,false,true,false,candidate);t.scenario("Glorybringer",5,5,false,false,false,false,candidate);}
  else{t.scenario("Ramses, Assassin Lord",5,3,false,false,true,true,candidate);t.scenario("Grizzly Bears",4,5,false,false,true,true,candidate);t.scenario("Goldspan Dragon",6,5,false,false,true,true,candidate);t.scenario("Grizzly Bears",5,5,false,false,true,false,candidate);t.scenario("Grizzly Bears",4,4,false,false,true,false,candidate);t.scenario("Grizzly Bears",4,5,true,false,true,false,candidate);t.scenario("Grizzly Bears",4,5,false,true,true,false,candidate);t.scenario("Grizzly Bears",4,5,false,false,false,false,candidate);}
  System.out.println("Checks passed: "+t.groups);System.exit(0);
 }
}
