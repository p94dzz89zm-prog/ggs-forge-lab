import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.combat.*;
import forge.game.phase.*;
import forge.game.player.*;
import org.testng.Assert;

public class AttackLimitRegression extends AITest {
 int checks;
 void crawlspace(boolean ggs,boolean disabled,boolean tax) {
  Game g=initAndCreateThreePlayerGame();Player ai=g.getPlayers().get(1);System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  System.setProperty("dragonmind.disableAttackLimitRecovery",Boolean.toString(disabled));
  if(ggs)addCard("Goro-Goro and Satoru",ai).setCommander(true);else System.clearProperty("forge.ai.ggsPilotPlayer");
  for(String n:new String[]{"Invisible Stalker","Invisible Stalker","Baleful Strix"}){Card c=addCard(n,ai);c.setSickness(false);c.setTurnInZone(-1);}
  for(Player p:ai.getOpponents()){addCard("Crawlspace",p);if(tax)addCard("Ghostly Prison",p);p.setLife(p.getId()==0?17:27,null);fillLibrary(p,10);}
  addCard("Dauthi Voidwalker",g.getPlayers().get(0));fillLibrary(ai,10);
  g.getAction().checkStateEffects(true);g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);
  Combat combat=new Combat(ai);g.getPhaseHandler().setCombat(combat);
  ((PlayerControllerAi)ai.getController()).getAi().declareAttackers(ai,combat);
  System.out.println("actual controller attackers="+combat.getAttackersAndDefenders());
  Assert.assertTrue(CombatUtil.validateAttackers(combat));Assert.assertEquals(combat.getAttackers().size(),disabled||tax?0:2,"Useful legal attacks, with actual stock/payment boundaries");
  checks++;System.out.println("PASS full controller ggs="+ggs+" disabled="+disabled+" tax="+tax);
 }
 void subset(String restriction,boolean fresh) {
  System.clearProperty("dragonmind.disableAttackLimitRecovery");Game g=initAndCreateGame();Player ai=g.getPlayers().get(1),opp=g.getPlayers().get(0);
  addCard("Goro-Goro and Satoru",ai);if(!restriction.isEmpty())addCard(restriction,opp);
  g.getPhaseHandler().devModeSet(PhaseType.COMBAT_DECLARE_ATTACKERS,ai,false);Combat c=new Combat(ai);g.getPhaseHandler().setCombat(c);Card selected=null;
  for(int i=0;i<3;i++){Card body=addCard("Invisible Stalker",ai);body.setSickness(false);body.setTurnInZone(fresh&&i==2?g.getPhaseHandler().getTurn():-1);c.addAttacker(body,opp);if(i==2)selected=body;}
  Assert.assertEquals(AttackLimitRecovery.repair(ai,c),!restriction.isEmpty());Assert.assertTrue(CombatUtil.validateAttackers(c));
  Assert.assertEquals(c.getAttackers().size(),restriction.isEmpty()?3:restriction.equals("Silent Arbiter")?1:2);
  if(fresh)Assert.assertTrue(c.isAttacking(selected));checks++;System.out.println("PASS cap="+restriction+" fresh="+fresh);
 }
 public static void main(String[]args){AttackLimitRegression t=new AttackLimitRegression();t.initializeModel();t.crawlspace(true,false,false);t.crawlspace(true,true,false);t.crawlspace(false,false,false);t.crawlspace(true,false,true);t.subset("Crawlspace",false);t.subset("Crawlspace",true);t.subset("Silent Arbiter",true);t.subset("",false);System.out.println("Checks passed: "+t.checks);System.exit(0);}
}
