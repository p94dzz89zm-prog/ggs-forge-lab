import com.google.gson.*;
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

/** Actual four-player stack/action/combat branches, not complete matches. */
public class MultiplayerCounterEvidence extends LearnedCounterHeldoutRegression {
 record Outcome(boolean countered,boolean survives,int life,boolean targetSurvives,
  boolean swanRetained,boolean blueUntapped,long birds,boolean attackLegal) {}
 Outcome branch(String body,String shield,boolean protect,int life,Boolean force,long seed,int hidden) {
  players=4;forge.util.MyRandom.setRandom(new Random(seed));Game g=initAndCreateThreePlayerGame();
  Player owner=g.getPlayers().get(0),ai=g.getPlayers().get(1),attacker=g.getPlayers().get(2),remover=g.getPlayers().get(3);
  for(Player p:g.getPlayers()){p.setLife(40,null);fillLibrary(p,20);}
  ai.setLife(life,null);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  System.setProperty("dragonmind.strategyProfile","BALANCED");
  Card blue=addCard("Watery Grave",ai);blue.setTapped(false);addCard("Blood Crypt",ai).setTapped(true);addCard("Skullclamp",ai);
  Card swan=addCardToZone("Swan Song",ai,ZoneType.Hand);
  for(String n:List.of("Balefire Dragon","Fire Navy Trebuchet","Flooded Strand","Goldlust Triad","Dragon Tempest"))addCardToZone(n,ai,ZoneType.Hand);
  for(int i=0;i<hidden;i++)addCardToZone(i%2==0?"Counterspell":"Dark Ritual",owner,ZoneType.Hand);
  Card threat=addCard(body,attacker);threat.setSickness(false);threat.setTurnInZone(-1);
  Card target=protect?addCard(shield,owner):threat;
  for(String n:List.of("Plains","Swamp","Shire Terrace"))addCard(n,remover);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,attacker,false);
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();
  removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));
  Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  String before=PlannerSnapshot.forPlayer(ai).toString();var rng=forge.util.MyRandom.getRandom();
  double[] features=GgsMultiplayerCounterFeatures.extract(ai);
  Assert.assertNotNull(features,"supported public contrast");
  Assert.assertEquals(features,new double[]{1,protect?1:-1},"independent public threat contrast");
  Assert.assertEquals(PlannerSnapshot.forPlayer(ai).toString(),before,"projection must not mutate live state");
  Assert.assertSame(forge.util.MyRandom.getRandom(),rng,"live RNG restored");
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();
  boolean automatic=choices!=null&&choices.stream().anyMatch(s->s.getHostCard()==swan);
  boolean counter=force==null?automatic:force;
  if(counter){SpellAbility sa=swan.getFirstSpellAbility();sa.setActivatingPlayer(ai);sa.getTargets().clear();sa.getTargets().add(removal);Assert.assertTrue(sa.canTargetSpellAbility(removal));Assert.assertTrue(ComputerUtilCost.canPayCost(sa,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));}
  drain(g);long birds=remover.getCreaturesInPlay().stream().filter(c->c.isToken()&&c.getName().contains("Bird")).count();
  Assert.assertEquals(target.isInZone(ZoneType.Battlefield),counter);Assert.assertEquals(swan.isInZone(ZoneType.Hand),!counter);Assert.assertEquals(blue.isTapped(),counter);Assert.assertEquals(birds,counter?1L:0L);
  boolean legal=threat.isInZone(ZoneType.Battlefield)&&CombatUtil.canAttack(threat,ai);
  Assert.assertEquals(legal,protect?!counter:counter);
  if(legal){Combat combat=new Combat(attacker);combat.addAttacker(threat,ai);combat.setBlocked(threat,false);g.getPhaseHandler().setCombat(combat);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_BLOCKERS,attacker,false);Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertTrue(ai.getCreaturesInPlay().isEmpty());combat.assignCombatDamage(false);combat.dealAssignedDamage();}
  Assert.assertEquals(ai.getLife(),legal?life-threat.getNetCombatDamage():life);
  boolean survives=ai.getLife()>0;Assert.assertEquals(survives,protect?counter:!counter);
  checks++;return new Outcome(counter,survives,ai.getLife(),target.isInZone(ZoneType.Battlefield),!counter,!counter,birds,legal);
 }
 public static void main(String[] args) {
  MultiplayerCounterEvidence t=new MultiplayerCounterEvidence();t.initializeModel();
  String purpose=args[0];boolean collect=purpose.equals("development");
  List<String> bodies=collect?List.of("Gigantosaurus","Ancient Brontodon"):List.of("Scaled Wurm","Enormous Baloth");
  String shield=collect?"Peacekeeper":"Stormtide Leviathan";
  int i=0;for(String body:bodies)for(int life:List.of(3,4,5))for(boolean protect:List.of(false,true)) {
   long seed=(collect?2026132200L:2026142200L)+i++;
   JsonObject row=new JsonObject();row.addProperty("id",purpose+":"+seed);row.addProperty("purpose",purpose);row.addProperty("scope","four_player_visible_survival_v1");row.addProperty("seed",seed);row.addProperty("target",protect?shield:body);row.addProperty("body",body);row.addProperty("life",life);row.addProperty("protecting_opposing_permanent",protect);row.addProperty("legal_paid_resolved",true);row.add("features",new Gson().toJsonTree(new double[]{1,protect?1:-1}));
   if(collect){row.add("counter_outcome",new Gson().toJsonTree(t.branch(body,shield,protect,life,true,seed,0)));row.add("pass_outcome",new Gson().toJsonTree(t.branch(body,shield,protect,life,false,seed,0)));}
   else row.add("actual",new Gson().toJsonTree(t.branch(body,shield,protect,life,null,seed,0)));
   System.out.println("MULTIPLAYER_DATA "+row);
  }
  if(args.length>1&&args[1].equals("visibility"))for(int hidden:List.of(0,7))t.branch("Gigantosaurus","Peacekeeper",true,4,true,2026132200L,hidden);
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
