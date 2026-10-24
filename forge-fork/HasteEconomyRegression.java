import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.*;
import forge.game.ability.*;
import forge.game.card.*;
import forge.game.keyword.*;
import forge.game.phase.*;
import forge.game.player.*;
import forge.game.spellability.*;
import org.testng.Assert;

/** Boundaries reconstructed from seed 2026107101, not a full-state replay. */
public class HasteEconomyRegression extends AITest {
 int checks;
 void check(int mode) {
  Game g=initAndCreateGame();Player ai=g.getPlayers().get(1);
  fillLibrary(ai,12);fillLibrary(g.getPlayers().get(0),12);
  System.setProperty("forge.ai.ggsPilotPlayer",ai.getName());
  System.clearProperty("dragonmind.disableRecoveryPolicy");
  Card ggs=addCard("Goro-Goro and Satoru",ai);ggs.setSickness(false);
  Card body=addCard("Balefire Dragon",ai);body.setSickness(false);
  for(int i=0;i<6;i++)addCard("Mountain",ai);
  SpellAbility sa=ggs.getSpellAbilities().stream().filter(x->x.getApi()==ApiType.PumpAll).findFirst().orElseThrow();
  sa.setActivatingPlayer(ai);
  if(mode==1||mode==2||mode==5)body.setSickness(true);
  if(mode==2)body.addIntrinsicKeyword("Haste");
  if(mode==3)System.clearProperty("forge.ai.ggsPilotPlayer");
  if(mode==4)System.setProperty("dragonmind.disableRecoveryPolicy","true");
  if(mode==5)body.setTapped(true);
  if(mode==7){sa.getMapParams().put("KW","Haste & Trample");}
  if(mode==8){sa.getMapParams().put("NumAtt","1");}
  g.getPhaseHandler().devModeSet(mode==6?PhaseType.UPKEEP:PhaseType.MAIN1,ai,false);
  AiController controller=((PlayerControllerAi)ai.getController()).getAi();
  Assert.assertEquals(GgsRecoveryPolicy.rejectRedundantHaste(ai,sa),mode==0||mode==2||mode==6,"guard boundary "+mode);
  AiPlayDecision decision=controller.canPlaySa(sa);
  if(mode==0||mode==2||mode==6)Assert.assertEquals(decision,AiPlayDecision.CantPlayAi,"pointless haste mode "+mode);
  if(mode==1)Assert.assertEquals(decision,AiPlayDecision.WillPlay,"fresh creature retains stock haste path");
  if(mode==3||mode==4||mode==5||mode==7||mode==8) {
   System.setProperty("dragonmind.disableRecoveryPolicy","true");
   Assert.assertEquals(decision,controller.canPlaySa(sa),"stock boundary "+mode);
  }
  checks++;System.out.println("PASS haste economy "+mode);
 }
 public static void main(String[] args) {
  HasteEconomyRegression t=new HasteEconomyRegression();t.initializeModel();
  for(int i=0;i<9;i++)t.check(i);
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
