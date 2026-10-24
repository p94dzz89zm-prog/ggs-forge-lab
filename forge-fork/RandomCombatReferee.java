import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import org.testng.Assert;
import java.util.*;

/** Seeded diverse board probes. Legality checks, not an optimal-play oracle. */
public class RandomCombatReferee extends AITest {
 void scenario(int seed) {
  Random rng=new Random(900000L+seed);forge.util.MyRandom.setRandom(new Random(900000L+seed));
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  System.setProperty("dragonmind.strategyProfile",List.of("BALANCED","ENGINE","ECONOMY").get(seed%3));
  g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);
  List<String> pool=List.of("Changeling Outcast","Gingerbrute","Phoenix Chick","Ornithopter","Runeclaw Bear","Colossal Dreadmaw","Tetsuko Umezawa, Fugitive","Baleful Strix","Invisible Stalker","Dauthi Voidwalker","Krenko, Tin Street Kingpin");
  if(seed%2==0)addCard("Goro-Goro and Satoru",ai).setCommander(true);
  for(int i=0;i<1+rng.nextInt(5);i++) {
   Card c=addCard(pool.get(rng.nextInt(pool.size())),ai);c.setSickness(rng.nextInt(4)==0);c.setTapped(rng.nextInt(5)==0);
   c.setTurnInZone(rng.nextBoolean()?g.getPhaseHandler().getTurn():-1);
  }
  for(Player p:ai.getOpponents()) {
   p.setLife(1+rng.nextInt(40),null);
   for(int i=0;i<rng.nextInt(5);i++){Card c=addCard(pool.get(rng.nextInt(pool.size())),p);c.setSickness(false);c.setTapped(rng.nextInt(4)==0);}
   if(seed%7==0)addCard("Ghostly Prison",p);
   if(seed%11==0)addCard("Propaganda",p);
   if(seed%17==0)addCard("Crawlspace",p);
   for(int i=0;i<4;i++)addCard("Island",p);
   fillLibrary(p,10);
  }
  if(seed%13==0)addCard("Ensnaring Bridge",ai);
  if(seed%19==0)addCard("Silent Arbiter",ai);
  if(seed%23==0)addCard("Goblin War Drums",ai);
  if(seed%29==0)addCard("Archetype of Imagination",ai);
  for(int i=0;i<4;i++)addCard("Mountain",ai);fillLibrary(ai,10);g.getAction().checkStateEffects(true);
  var before=new HashMap<Integer,String>();
  for(Card c:g.getCardsIn(forge.game.zone.ZoneType.Battlefield))before.put(c.getId(),c.getController().getId()+":"+c.isTapped()+":"+c.getNetPower()+":"+c.getNetToughness());
  Combat combat=new Combat(ai);g.getPhaseHandler().setCombat(combat);((PlayerControllerAi)ai.getController()).getAi().declareAttackers(ai,combat);
  if(!CombatUtil.validateAttackers(combat)) {
   System.out.println("FAIL BOARD seed="+seed+" profile="+System.getProperty("dragonmind.strategyProfile"));
   for(Player p:g.getPlayers())System.out.println("PLAYER "+p+" life="+p.getLife()+" cards="+p.getCardsIn(forge.game.zone.ZoneType.Battlefield));
   System.out.println("ATTACKS "+combat.getAttackersAndDefenders()+" violations="+combat.getAttackConstraints().countViolations(combat.getAttackersAndDefenders())+" legal="+combat.getAttackConstraints().getLegalAttackers());
  }
  Assert.assertTrue(CombatUtil.validateAttackers(combat),"illegal attackers seed "+seed);
  for(Card c:combat.getAttackers()) {
   Assert.assertEquals(c.getController(),ai);Assert.assertFalse(c.isTapped());
   Assert.assertTrue(CombatUtil.canAttack(c,combat.getDefenderByAttacker(c)));
  }
  var after=new HashMap<Integer,String>();
  for(Card c:g.getCardsIn(forge.game.zone.ZoneType.Battlefield))after.put(c.getId(),c.getController().getId()+":"+c.isTapped()+":"+c.getNetPower()+":"+c.getNetToughness());
  Assert.assertEquals(after,before,"forecast mutated board seed "+seed);
  for(Player p:ai.getOpponents()) {
   new AiBlockController(p,false).assignBlockersForCombat(combat);
   Assert.assertNull(CombatUtil.validateBlocks(combat,p),"illegal blocks seed "+seed);
  }
  System.out.println("PASS random combat seed="+seed+" profile="+System.getProperty("dragonmind.strategyProfile")+" attackers="+combat.getAttackers().size());
 }
 public static void main(String[] args){int count=args.length>0?Integer.parseInt(args[0]):64;int start=args.length>1?Integer.parseInt(args[1]):0;if(count<1)throw new IllegalArgumentException("Positive scenario count required");RandomCombatReferee r=new RandomCombatReferee();r.initializeModel();for(int s=start;s<start+count;s++)r.scenario(s);System.out.println("Checks passed: "+count);System.exit(0);}
}
