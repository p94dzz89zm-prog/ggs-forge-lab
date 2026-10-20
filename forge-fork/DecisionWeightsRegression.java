import forge.ai.ggs.*;
import org.testng.Assert;

public class DecisionWeightsRegression {
 public static void main(String[] args) {
  String[] keys={"damage","hitPercent","dragon","mana","replay","bodyDivisor"};
  int checks=0;
  for(String key:keys)System.clearProperty("dragonmind.weight."+key);
  for(String profile:new String[]{"BALANCED","ENGINE","ECONOMY"}) {
   System.setProperty("dragonmind.strategyProfile",profile);
   var s=AdaptiveStrategy.current();var w=DecisionWeights.current();
   Assert.assertEquals(w.damage(),10);Assert.assertEquals(w.hitPercent(),100);
   Assert.assertEquals(w.dragon(),s.dragonBonus);Assert.assertEquals(w.mana(),s.manaPenalty);Assert.assertEquals(w.replay(),s.replayPenalty);Assert.assertEquals(w.bodyDivisor(),8);checks++;
  }
  int[] lo={4,25,0,0,0,4},hi={20,200,180,16,16,16};
  for(int i=0;i<keys.length;i++) {
   String prop="dragonmind.weight."+keys[i];
   System.setProperty(prop,""+lo[i]);DecisionWeights.current();
   System.setProperty(prop,""+hi[i]);DecisionWeights.current();checks++;
   System.setProperty(prop,""+(hi[i]+1));
   try{DecisionWeights.current();throw new AssertionError("bad bound accepted");}catch(IllegalArgumentException expected){}checks++;
   System.setProperty(prop,"NaN");
   try{DecisionWeights.current();throw new AssertionError("bad weight accepted");}catch(IllegalArgumentException expected){}checks++;
   System.clearProperty(prop);
  }
  System.out.println("Checks passed: "+checks);System.exit(0);
 }
}
