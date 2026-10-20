import forge.ai.*;
import forge.ai.ggs.*;
import forge.game.card.*;
import forge.game.phase.*;
import forge.game.spellability.*;
import forge.game.zone.*;
import org.testng.Assert;
import java.util.*;

/** Fresh paired response fixtures; not natural games or all-deck coverage. */
public class ProtectionManaHeldoutRegression extends ProtectionManaRegression {
 int evaluated;
 void heldout(int mode,boolean baseline) {
  String threat=mode==2?"Royal Assassin":"Visara the Dreadful";
  Board b=board(threat,mode==1?3:mode==3?4:2,false,false);
  if(mode==2)b.commander().setTapped(true);
  b.p().setLife(17,null);
  System.setProperty("dragonmind.linePlanner","true");System.setProperty("dragonmind.linePlannerMillis","60000");
  String before=PlannerSnapshot.forPlayer(b.p()).toString();var chosen=((PlayerControllerAi)b.p().getController()).getAi().chooseSpellAbilityToPlay();Assert.assertEquals(PlannerSnapshot.forPlayer(b.p()).toString(),before);
  if(chosen!=null){Assert.assertEquals(chosen.size(),1);Assert.assertTrue(chosen.get(0).canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(chosen.get(0),b.p(),false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),chosen.get(0),null));LinePlannerRegression.drain(b.g());}
  var kill=removal(b);Assert.assertTrue(kill.canPlay());Assert.assertTrue(kill.canTarget(b.commander()));Assert.assertTrue(ComputerUtilCost.canPayCost(kill,b.enemy(),false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.enemy(),kill,null));Assert.assertTrue(b.removal().isTapped());
  var response=((PlayerControllerAi)b.p().getController()).getAi().chooseSpellAbilityToPlay();
  if(response!=null){Assert.assertEquals(response.size(),1);var save=response.get(0);Assert.assertEquals(save.getHostCard().getName(),"March of Swirling Mist");Assert.assertTrue(save.getTargets().getTargetCards().contains(b.commander()));Assert.assertTrue(save.canPlay());Assert.assertTrue(ComputerUtilCost.canPayCost(save,b.p(),false));Assert.assertTrue(ComputerUtil.handlePlayingSpellAbility(b.p(),save,null));}
  LinePlannerRegression.drain(b.g());boolean retained=b.g().getCardsIncludePhasingIn(ZoneType.Battlefield).anyMatch(c->c.getId()==b.commander().getId());
  System.out.println("HELDOUT_RESPONSE mode="+mode+" threat="+threat+" baseline="+baseline+" action="+chosen+" response="+response+" retained="+retained);
  Assert.assertEquals(retained,!baseline);if(!baseline){Assert.assertTrue(b.commander().isPhasedOut());Assert.assertNotNull(response);}
  System.clearProperty("dragonmind.linePlanner");System.clearProperty("dragonmind.linePlannerMillis");evaluated++;
 }
 public static void main(String[]args){if(args.length<2||!args[0].equals("--purpose")||!args[1].equals("heldout"))throw new IllegalArgumentException("Requires --purpose heldout");boolean baseline=Arrays.asList(args).contains("--baseline");ProtectionManaHeldoutRegression t=new ProtectionManaHeldoutRegression();t.initializeModel();for(int m=0;m<4;m++)t.heldout(m,baseline);System.out.println("Checks passed: "+t.evaluated);System.exit(0);}
}
