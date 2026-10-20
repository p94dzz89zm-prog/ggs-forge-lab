import com.google.gson.*;
import forge.ai.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Actual paid/resolved decision pairs. Constructed diagnostics, never full games. */
public class LearnedCounterPreferenceRegression extends AITest {
 int checks;
 record Outcome(boolean targetSurvives,boolean swanRetained,boolean blueUntapped,long birds,int life,int power) {}
 void drain(Game g){for(int i=0;i<40;i++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new AssertionError("stack cap");}
 Outcome play(String name,boolean own,Boolean force,boolean learned,int life){
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1),enemy=g.getPlayers().get(0),remover=g.getPlayers().get(2);
  for(Player p:g.getPlayers())fillLibrary(p,20);
  ai.setLife(life,null);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());System.setProperty("dragonmind.strategyProfile","BALANCED");
  Card blue=addCard("Watery Grave",ai);blue.setTapped(false);addCard("Blood Crypt",ai).setTapped(true);addCard("Skullclamp",ai);
  Card swan=addCardToZone("Swan Song",ai,ZoneType.Hand);
  for(String n:List.of("Balefire Dragon","Fire Navy Trebuchet","Flooded Strand","Goldlust Triad","Dragon Tempest"))addCardToZone(n,ai,ZoneType.Hand);
  Card target=addCard(name,own?ai:enemy);
  for(String n:List.of("Plains","Swamp","Shire Terrace"))addCard(n,remover);
  g.getPhaseHandler().devModeSet(PhaseType.MAIN1,remover,false);
  SpellAbility removal=addCardToZone("Mortify",remover,ZoneType.Hand).getFirstSpellAbility();removal.setActivatingPlayer(remover);removal.getTargets().add(target);
  Assert.assertTrue(removal.canTarget(target));Assert.assertTrue(ComputerUtilCost.canPayCost(removal,remover,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(remover,removal,null));
  Assert.assertEquals(remover.getLandsInPlay().stream().filter(Card::isTapped).count(),3L);
  var choices=((PlayerControllerAi)ai.getController()).getAi().chooseSpellAbilityToPlay();boolean automatic=choices!=null&&choices.stream().anyMatch(s->s.getHostCard()==swan);
  if(force==null)Assert.assertEquals(automatic,learned&&!own?false:true,"actual-controller heldout choice "+name+" own="+own);
  boolean counter=force==null?automatic:force;
  if(counter){SpellAbility sa=swan.getFirstSpellAbility();sa.setActivatingPlayer(ai);sa.getTargets().clear();sa.getTargets().add(removal);Assert.assertTrue(sa.canTargetSpellAbility(removal));Assert.assertTrue(ComputerUtilCost.canPayCost(sa,ai,false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(ai,sa,null));}
  drain(g);long birds=remover.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.isToken()&&c.getName().contains("Bird")&&c.getNetPower()==2&&c.getNetToughness()==2).count();
  Assert.assertEquals(target.isInZone(ZoneType.Battlefield),counter);Assert.assertEquals(swan.isInZone(ZoneType.Hand),!counter);Assert.assertEquals(blue.isTapped(),counter);Assert.assertEquals(birds,counter?1L:0L);Assert.assertEquals(ai.getLife(),life);
  checks++;return new Outcome(counter,!counter,!counter,birds,ai.getLife(),target.getNetPower());
 }
 void pair(String name,boolean own,int power,int life){
  Outcome counter=play(name,own,true,false,life),pass=play(name,own,false,false,life);
  JsonObject r=new JsonObject();r.addProperty("id","development:"+name+":"+own);r.addProperty("purpose","development");r.addProperty("scope","scoped_counterspell_preference_v1");r.addProperty("legal_paid_resolved",true);
  r.add("features",new Gson().toJsonTree(new double[]{1,own?1:-1,counter.power()/10.0,life/40.0}));r.add("counter_outcome",new Gson().toJsonTree(counter));r.add("pass_outcome",new Gson().toJsonTree(pass));r.addProperty("target_card",name);r.addProperty("target_owned",own);
  System.out.println("TACTICAL_DATA "+r);
 }
 public static void main(String[]args){LearnedCounterPreferenceRegression t=new LearnedCounterPreferenceRegression();t.initializeModel();
  if(args[0].equals("collect")){for(boolean own:List.of(false,true)){t.pair("Ezio Auditore da Firenze",own,3,38);t.pair("Hill Giant",own,3,36);t.pair("Goro-Goro and Satoru",own,3,34);}}
  else if(args[0].equals("continuous-control")){t.play("Peacekeeper",false,null,false,38);}
  else {boolean learned=args[0].equals("learned");int life=args[0].equals("out-of-scope")?25:38;for(boolean own:List.of(false,true)){t.play("Baleful Strix",own,null,learned,life);t.play("Krenko, Tin Street Kingpin",own,null,learned,life);}}
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
