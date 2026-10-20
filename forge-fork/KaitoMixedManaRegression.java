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

/** Critical public features from the saved turn49, not a whole-game replay.
 * Private hands, unknown Thriving choices and unrelated permanents are omitted.
 * The unambiguous printed black sources suffice without those choices.
 */
public class KaitoMixedManaRegression extends PackageRecoveryRegression {
 public record Position(Game game,Player ai,Player opponent,Card kaito,Card threat,Card regalia,Card sword){}
 Position original(){
  Game g=initAndCreateThreePlayerGame();g.EXPERIMENTAL_RESTORE_SNAPSHOT=false;Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(2);for(Player p:g.getPlayers())fillLibrary(p,90);ai.setLife(7,null);g.getPlayers().get(0).setLifeLostThisTurn(9);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.linePlanner","false");System.setProperty("dragonmind.strategyProfile","BALANCED");
  Card commander=addCard("Goro-Goro and Satoru",ai);commander.setSickness(false);commander.setTurnInZone(-1);commander.setCommander(true);ai.addCommander(commander);
  addToken("r_5_5_dragon_spirit_flying",ai);Card dragon=addToken("r_5_5_dragon_spirit_flying",ai);dragon.setTapped(true);Card goldspan=addCard("Goldspan Dragon",ai);goldspan.setTapped(true);
  Card ramses=addCard("Ramses, Assassin Lord",opp),threat=addCard("Combustion Man",opp),regalia=addCard("Brotherhood Regalia",opp),sword=addCard("Vorpal Sword",opp);for(Card c:List.of(ramses,threat)){c.setSickness(false);c.setTurnInZone(-1);}
  Card ezio=addCardToZone("Ezio Auditore da Firenze",opp,ZoneType.Command);ezio.setCommander(true);opp.addCommander(ezio);opp.initCommanderColor(ezio);
  for(String name:List.of("Abstergo Entertainment","Plains","Submerged Boneyard","Thriving Moor","Exotic Orchard","Island","Path of Ancestry","Thriving Grove","Mountain"))addCard(name,opp).setTapped(true);
  for(String name:List.of("Island","Island","Swamp","Swamp"))addCard(name,ai);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN2,ai,false);g.getAction().checkStateEffects(true);Assert.assertEquals(threat.getNetPower(),5);Assert.assertEquals(threat.getNetToughness(),7);
  Card kaito=cast(ai,addCardToZone("Kaito, Bane of Nightmares",ai,ZoneType.Hand));Assert.assertEquals(ai.getLandsInPlay().stream().filter(Card::isTapped).count(),4L);Assert.assertEquals(opp.getLandsInPlay().stream().filter(Card::isTapped).count(),9L);
  System.out.println("MIXED originalPT="+threat.getNetPower()+"/"+threat.getNetToughness()+" boostTable="+threat.getPTBoostTable());
  return new Position(g,ai,opp,kaito,threat,regalia,sword);
 }
 static void nextMain(Position p){
  Game g=p.game();Player opp=p.opponent();g.getPhaseHandler().devModeSet(PhaseType.UNTAP,opp,false);
  for(Card land:opp.getLandsInPlay())if(land.isTapped())land.untap(opp);
  if(p.threat().isTapped())p.threat().untap(opp);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,opp,false);g.getAction().checkStateEffects(true);
 }
 void equip(Position p,boolean observedCost){
  for(Card equipment:List.of(p.regalia(),p.sword())){
   SpellAbility sa=equipment.getSpellAbilities().stream().peek(a->a.setActivatingPlayer(p.opponent())).filter(a->a.getApi()==ApiType.Attach&&a.canTarget(p.threat())).filter(a->!observedCost||equipment!=p.regalia()||a.getPayCosts().getTotalMana().getCMC()==3).min(Comparator.comparingInt(a->a.getPayCosts().getTotalMana().getCMC())).orElseThrow();
   Assert.assertTrue(sa.canPlay());Assert.assertTrue(sa.canTarget(p.threat()));sa.getTargets().add(p.threat());play(p.opponent(),sa);Assert.assertEquals(equipment.getEquipping(),p.threat());
  }
  Assert.assertEquals(p.threat().getNetPower(),7);Assert.assertEquals(p.opponent().getLandsInPlay().stream().filter(Card::isTapped).count(),observedCost?5L:3L,"actual combined equip payment from distinct mana sources");
 }
 void run(String mode,boolean observedCost){
  Position p=original();String before=PlannerSnapshot.forPlayer(p.ai()).toString();var choices=((PlayerControllerAi)p.ai().getController()).getAi().chooseSpellAbilityToPlay();Assert.assertNotNull(choices);Assert.assertEquals(choices.size(),1);SpellAbility action=choices.get(0);Assert.assertEquals(action.getHostCard(),p.kaito());
  boolean defensive=!mode.equals("baseline");if(mode.equals("counterfactual")){Assert.assertEquals(action.getApi(),ApiType.Surveil);action=p.kaito().getSpellAbilities().stream().filter(a->a.getApi()==ApiType.Tap).findFirst().orElseThrow();action.setActivatingPlayer(p.ai());Assert.assertTrue(action.canTarget(p.threat()));action.getTargets().add(p.threat());}
  Assert.assertEquals(action.getApi(),defensive?ApiType.Tap:ApiType.Surveil,"actual controller must reserve Kaito for the mixed-mana public threat");Assert.assertEquals(PlannerSnapshot.forPlayer(p.ai()).toString(),before,"selection/forecast cannot mutate live public state or own hand");
  if(defensive)Assert.assertEquals(action.getTargetCard(),p.threat());play(p.ai(),action);if(defensive){Assert.assertEquals(p.kaito().getCounters(CounterEnumType.LOYALTY),2);Assert.assertEquals(p.threat().getCounters(CounterEnumType.STUN),2);}
  nextMain(p);equip(p,observedCost);
  if(defensive){Assert.assertTrue(p.threat().isTapped());Assert.assertEquals(p.threat().getCounters(CounterEnumType.STUN),1);Assert.assertFalse(CombatUtil.canAttack(p.threat(),p.ai()));Assert.assertEquals(p.ai().getLife(),7);}
  else{Assert.assertTrue(CombatUtil.canAttack(p.threat(),p.ai()));Combat combat=new Combat(p.opponent());combat.addAttacker(p.threat(),p.ai());combat.setBlocked(p.threat(),false);p.game().getPhaseHandler().setCombat(combat);p.game().getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,p.opponent(),false);Assert.assertTrue(CombatUtil.validateAttackers(combat));for(Card c:p.ai().getCreaturesInPlay())Assert.assertFalse(CombatUtil.canBlock(p.threat(),c));combat.assignCombatDamage(false);combat.dealAssignedDamage();Assert.assertEquals(p.ai().getLife(),0);}
  groups++;System.out.println("MIXED mode="+mode+" observedEquip3="+observedCost+" life="+p.ai().getLife()+" paid="+(observedCost?5:3));
 }
 void controls(){
  for(String condition:List.of("one-black","two-total","stun-lands","temporary-power")){
   Position p=original();
   if(condition.equals("temporary-power"))p.threat().addPTBoost(1,0,999999,0);
   else{
    for(Card c:new ArrayList<Card>(p.opponent().getLandsInPlay()))p.game().getAction().moveToGraveyard(c,null);
    List<String> names=condition.equals("one-black")?List.of("Swamp","Island","Island","Island","Island"):condition.equals("two-total")?List.of("Swamp","Swamp"):List.of("Swamp","Swamp","Swamp","Swamp","Swamp");
    for(String name:names){Card land=addCard(name,p.opponent());land.setTapped(true);if(condition.equals("stun-lands"))land.setCounters(CounterType.getType("Stun"),2);}
   }
   p.game().getAction().checkStateEffects(true);String before=PlannerSnapshot.forPlayer(p.ai()).toString();var rng=forge.util.MyRandom.getRandom();
   Assert.assertFalse(GgsKaitoThreatPolicy.executableEquipmentLine(p.ai(),p.threat()),condition);
   Assert.assertSame(forge.util.MyRandom.getRandom(),rng,"forecast restores live RNG object");Assert.assertEquals(PlannerSnapshot.forPlayer(p.ai()).toString(),before,"forecast leaves live state unchanged");groups++;System.out.println("MIXED control="+condition);
  }
 }
 void privacy(){
  for(String secret:List.of("Force of Will","Counterspell","Swords to Plowshares")){
   Position p=original();addCardToZone(secret,p.opponent(),ZoneType.Hand);String before=PlannerSnapshot.forPlayer(p.ai()).toString();var previous=forge.util.MyRandom.getRandom();
   try{forge.util.MyRandom.setRandom(new Random(7317));Assert.assertTrue(GgsKaitoThreatPolicy.executableEquipmentLine(p.ai(),p.threat()),"same public line despite hidden variation");Assert.assertEquals(forge.util.MyRandom.getRandom().nextLong(),new Random(7317).nextLong(),"forecast cannot advance live RNG state");Assert.assertEquals(PlannerSnapshot.forPlayer(p.ai()).toString(),before,"forecast cannot mutate live state");}
   finally{forge.util.MyRandom.setRandom(previous);}groups++;
  }
 }
 public static void main(String[]args){var t=new KaitoMixedManaRegression();t.initializeModel();if(args[0].equals("privacy"))t.privacy();else if(args[0].equals("controls"))t.controls();else{t.run(args[0],false);t.run(args[0],true);}System.out.println("Checks passed: "+t.groups);System.exit(0);}
}
