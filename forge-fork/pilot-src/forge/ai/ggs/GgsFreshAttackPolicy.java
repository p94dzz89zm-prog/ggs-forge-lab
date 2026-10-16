package forge.ai.ggs;
import forge.ai.ComputerUtilCombat;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.player.Player;

/** Supplement stock attacks with one small, fresh, currently open GGS connection. */
public final class GgsFreshAttackPolicy {
 private GgsFreshAttackPolicy() {}
 private static boolean open(Card c,Player p) {
  for(Card blocker:p.getCreaturesInPlay())if(CombatUtil.canBlock(c,blocker))return false;
  return ComputerUtilCombat.predictDamageTo(p,c.getNetCombatDamage(),c,true)>0;
 }
 public static void supplement(Player ai,Combat combat) {
  if(!GgsNinjutsuPolicy.enabled(ai)||Boolean.getBoolean("dragonmind.disableFreshAttackPolicy")
   ||combat.getAttackingPlayer()!=ai||!ai.getCreaturesInPlay().anyMatch(CommanderEngineProfile::needsFreshCombatConnection))return;
  var choices=new java.util.ArrayList<Card>(ai.getCreaturesInPlay());
  choices.sort(java.util.Comparator.comparingInt(Card::getId));
  for(Card fresh:choices) {
   if(!fresh.enteredThisTurn()||combat.isAttacking(fresh)||fresh.getNetCombatDamage()<=0
    ||fresh.getNetCombatDamage()>(combat.getAttackers().isEmpty()?5:2))continue;
   for(Player defender:ai.getOpponents()) {
    boolean covered=false;
    for(Card old:combat.getAttackers())if(old.enteredThisTurn()&&combat.getDefenderByAttacker(old)==defender&&open(old,defender))covered=true;
    if(covered||!CombatUtil.canAttack(fresh,defender)||CombatUtil.getAttackCost(ai.getGame(),fresh,defender)!=null||!open(fresh,defender))continue;
    combat.addAttacker(fresh,defender);
    if(CombatUtil.validateAttackers(combat))return;
    combat.removeFromCombat(fresh);
   }
  }
 }
}
