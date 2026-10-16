package forge.ai.ggs;

import forge.game.GameEntity;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.player.Player;
import java.util.*;

/** Preserve a useful legal subset when an attack proposal exceeds a global cap.
 * Bounded search over already proposed attacks; no new defenders, hidden data,
 * relaxed requirements, or changed card rules. Stock fallback handles other cases.
 */
public final class AttackLimitRecovery {
 private AttackLimitRecovery() {}
 public static boolean repair(Player ai,Combat combat) {
  try(var inspection=ai.getGame().getReplacementHandler().beginReadOnlyCombatInspection()) {
  if(Boolean.getBoolean("dragonmind.disableAttackLimitRecovery"))return false;
  Map<Card,GameEntity> original=new LinkedHashMap<>(combat.getAttackersAndDefenders());
  var constraints=combat.getAttackConstraints();
  if(original.size()<2||original.size()>10||constraints.getGlobalRestrictions().isLegal(original))return false;
  var cards=new ArrayList<>(original.keySet());cards.sort(Comparator.comparingInt(Card::getId));
  for(Card c:cards)if(combat.getBandOfAttacker(c)!=null&&combat.getBandOfAttacker(c).getAttackers().size()>1)return false;
  int minimum=constraints.getLegalAttackers().getRight();
  boolean ggs=ai.getCreaturesInPlay().anyMatch(CommanderEngineProfile::needsFreshCombatConnection);
  Set<Card> freshOpen=new HashSet<>();
  if(ggs)for(Card c:cards) {
   if(!c.enteredThisTurn()||c.getNetCombatDamage()<=0||!(original.get(c) instanceof Player defender))continue;
   boolean open=true;for(Card blocker:defender.getCreaturesInPlay())if(CombatUtil.canBlock(c,blocker)){open=false;break;}
   if(open&&forge.ai.ComputerUtilCombat.predictDamageTo(defender,c.getNetCombatDamage(),c,true)>0)freshOpen.add(c);
  }
  Map<Card,GameEntity> best=null;long bestScore=Long.MIN_VALUE;
  for(int mask=1;mask<(1<<cards.size());mask++) {
   Map<Card,GameEntity> candidate=new LinkedHashMap<>();long score=0;Set<GameEntity> covered=new HashSet<>();
   for(int i=0;i<cards.size();i++)if((mask&(1<<i))!=0){
    Card c=cards.get(i);candidate.put(c,original.get(c));score+=10L*Math.max(0,c.getNetCombatDamage())+1;
    if(freshOpen.contains(c)&&covered.add(original.get(c)))score+=200;
   }
   int violations=constraints.countViolations(candidate);
   if(violations<0||violations>minimum)continue;
   if(score>bestScore){bestScore=score;best=candidate;}
  }
  if(best==null)return false;
  combat.clearAttackers();for(var e:best.entrySet())combat.addAttacker(e.getKey(),e.getValue());
  if(!CombatUtil.validateAttackers(combat)) {
   combat.clearAttackers();for(var e:original.entrySet())combat.addAttacker(e.getKey(),e.getValue());return false;
  }
  System.out.println("DragonMind AttackRepair: global-limit proposed="+original.size()+" preserved="+best.size());
  return true;
  }
 }
}
