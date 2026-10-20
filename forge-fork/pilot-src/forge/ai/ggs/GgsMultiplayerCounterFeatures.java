package forge.ai.ggs;

import forge.ai.simulation.GameCopier;
import forge.game.Game;
import forge.game.ability.ApiType;
import forge.game.combat.CombatUtil;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;

/** Bounded public-information threat contrast, not a win-probability estimate.
 * Projects the visible stack only. No draws, invented attacks, cooperation or
 * hidden responses. Exposure means one currently legal unblocked lethal body.
 */
public final class GgsMultiplayerCounterFeatures {
 private GgsMultiplayerCounterFeatures() {}
 private static boolean exposed(Player viewer) {
  Player active=viewer.getGame().getPhaseHandler().getPlayerTurn();
  if(!active.isOpponentOf(viewer))return false;
  return active.getCreaturesInPlay().stream().anyMatch(c->
   CombatUtil.canAttack(c,viewer)&&c.getNetCombatDamage()>=viewer.getLife()
    &&viewer.getCreaturesInPlay().stream().noneMatch(b->CombatUtil.canBlock(c,b)));
 }
 private static void drain(Game g) {
  for(int n=0;n<32;n++) {
   g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();
   g.getStack().addAllTriggeredAbilitiesToStack();
   if(g.getStack().isEmpty())return;g.getStack().resolveStack();
  }
  throw new IllegalStateException("public-stack-projection-cap");
 }
 /** Null is unsupported. A positive contrast means removal exposes us; a
  * negative contrast means removal eliminates the current visible exposure.
  * It is a threat possibility, never a prediction of an opponent's intention.
  */
 public static double[] extract(Player viewer) {
  Game live=viewer.getGame();
  if(PlannerContext.active()||live.getPlayers().size()!=4||live.getStack().size()!=1)return null;
  SpellAbility removal=live.getStack().peekAbility();
  if(removal==null||removal.getApi()!=ApiType.Destroy||removal.getSubAbility()!=null
    ||removal.getTargets().getTargetCards().size()!=1)return null;
  long started=System.nanoTime();
  try(PlannerContext ignored=PlannerContext.enter(220022)) {
   GameCopier copier=new GameCopier(live);Game projected=copier.makeCopy(null,viewer,true);
   if(projected.getStack().size()!=1)return null;
   Player self=copier.find(viewer);boolean before=exposed(self);drain(projected);
   if(System.nanoTime()-started>1_000_000_000L||self.hasLost())return null;
   boolean after=exposed(self);
   return new double[]{1.0,(after?1.0:0.0)-(before?1.0:0.0)};
  }catch(RuntimeException unsupported){return null;}
 }
}
