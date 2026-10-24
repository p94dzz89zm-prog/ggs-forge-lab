import forge.ai.*;import forge.game.*;import forge.game.card.*;import forge.game.combat.*;import forge.game.player.*;import org.testng.Assert;import java.io.*;import java.nio.charset.StandardCharsets;
public class BoundedForecastRegression extends AITest {
 int checks;void pass(String n){System.out.println("PASS "+n);checks++;}
 void scenario(String name,int attackCount,int blockCount,String keyword,boolean real,boolean disable,boolean bounded,int minBlocks) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);Combat combat=new Combat(opp);
  for(int i=0;i<blockCount;i++){Card c=addCard("Runeclaw Bear",ai);c.setSickness(false);}
  for(int i=0;i<attackCount;i++){Card c=addCard("Runeclaw Bear",opp);c.setSickness(false);if(!keyword.isEmpty()&&(name.equals("lure")?i==0:true))c.addIntrinsicKeyword(keyword);combat.addAttacker(c,ai);}
  if(real)g.getPhaseHandler().setCombat(combat);
  ByteArrayOutputStream captured=new ByteArrayOutputStream();PrintStream previous=System.out;
  if(disable)System.setProperty("dragonmind.boundedCombatForecast","false");
  try{System.setOut(new PrintStream(captured));new AiBlockController(ai,false).assignBlockersForCombat(combat);}finally{System.setOut(previous);System.clearProperty("dragonmind.boundedCombatForecast");}
  String log=captured.toString(StandardCharsets.UTF_8);Assert.assertEquals(log.contains("DragonMind Forecast: bounded"),bounded);
  Assert.assertNull(CombatUtil.validateBlocks(combat,ai));
  for(Card a:combat.getAttackers())if(!combat.getBlockers(a).isEmpty())Assert.assertTrue(combat.getBlockers(a).size()>=minBlocks);
  if(name.equals("lure"))Assert.assertEquals(combat.getBlockers(combat.getAttackers().get(0)).size(),blockCount);
  if(name.equals("flying"))Assert.assertTrue(combat.getAllBlockers().isEmpty());
  pass(name+": legal assignments and correct forecast gate");
 }
 public static void main(String[]args){BoundedForecastRegression t=new BoundedForecastRegression();t.initializeModel();
  t.scenario("large ordinary",24,24,"",false,false,true,1);
  t.scenario("menace",24,24,"Menace",false,false,true,2);
  t.scenario("lure",24,24,"All creatures able to block CARDNAME do so.",false,false,true,1);
  t.scenario("flying",24,24,"Flying",false,false,true,1);
  t.scenario("actual combat",24,24,"",true,false,false,1);
  t.scenario("disabled",24,24,"",false,true,false,1);
  t.scenario("budget boundary",4,8,"",false,false,false,1);
  t.scenario("above budget",5,8,"",false,false,true,1);
  System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
