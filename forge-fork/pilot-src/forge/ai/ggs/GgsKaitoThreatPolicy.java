package forge.ai.ggs;

import forge.ai.ComputerUtilCost;
import forge.ai.ComputerUtil;
import forge.ai.simulation.GameCopier;
import forge.game.Game;
import forge.game.combat.CombatUtil;
import forge.game.card.CounterEnumType;
import forge.game.zone.ZoneType;
import java.util.Comparator;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.util.List;

/** Bounded public equipment-line survival guard, not a future-turn solver.
 * Projects only untap and two visible equip actions in a masked game copy.
 * No draws, hidden interaction or intervening player actions are predicted.
 * Sequential real payment prevents double-counting colored mana sources.
 */
public final class GgsKaitoThreatPolicy {
 private GgsKaitoThreatPolicy() {}
 private static void drain(Game g) {
  for(int n=0;n<32;n++) {
   g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();
   g.getStack().addAllTriggeredAbilitiesToStack();
   if(g.getStack().isEmpty())return;g.getStack().resolveStack();
  }
  throw new IllegalStateException("equipment-resolution-cap");
 }
 private static boolean equip(Player owner,String name,Card target) {
  for(Card equipment:owner.getCardsIn(ZoneType.Battlefield)) {
   if(!equipment.getName().equals(name)||equipment.isEquipping()||equipment.isPhasedOut())continue;
   SpellAbility chosen=equipment.getSpellAbilities().stream().peek(sa->sa.setActivatingPlayer(owner))
    .filter(sa->sa.getApi()==ApiType.Attach&&sa.canTarget(target)&&sa.getPayCosts().isOnlyManaCost())
    .min(Comparator.comparingInt(sa->sa.getPayCosts().getTotalMana().getCMC())).orElse(null);
   if(chosen==null)return false;chosen.resetTargets();chosen.getTargets().add(target);
   if(!chosen.canPlay()||!ComputerUtilCost.canPayCost(chosen,owner,false)
      ||!ComputerUtil.handlePlayingSpellAbility(owner,chosen,null))return false;
   drain(owner.getGame());return equipment.getEquipping()==target;
  }
  return false;
 }
 /** Tests may inspect the same public-only forecast used by the controller.
  * False also means unsupported, unpayable, or budget exceeded; never safe.
  */
 public static boolean executableEquipmentLine(Player viewer,Card liveThreat) {
  long start=System.nanoTime();
  // Copies do not reconstruct scheduled cleanup callbacks. Reject nonstatic
  // P/T modifications rather than carrying an until-EOT pump into next turn.
  if(liveThreat.getPTBoostTable().containsColumn(0L)
    ||liveThreat.getSetPTTable().containsColumn(0L))return false;
  try(PlannerContext ignored=PlannerContext.enter(171017)) {
   GameCopier copier=new GameCopier(viewer.getGame());Game g=copier.makeCopy(null,viewer);
   Card threat=copier.find(liveThreat);Player owner=threat.getController(),defender=copier.find(viewer);
   owner.getManaPool().resetPool();
   g.getPhaseHandler().devModeSet(PhaseType.UNTAP,owner,false);
   for(Card land:owner.getLandsInPlay())if(land.isTapped()&&!land.isPhasedOut()
       &&land.canUntap(owner,false))land.untap(owner);
   g.getPhaseHandler().devModeSet(PhaseType.MAIN1,owner,false);drain(g);
   if(System.nanoTime()-start>1_000_000_000L)return false;
   // Pay the constrained BB cost first; generic equip must not consume it.
   if(!equip(owner,"Vorpal Sword",threat)||!equip(owner,"Brotherhood Regalia",threat))return false;
   if(System.nanoTime()-start>1_000_000_000L)return false;
   // Pure equip line: no substitute for full attack-trigger/prevention review.
   return CombatUtil.canAttack(threat,defender)&&threat.getNetPower()>=defender.getLife()
    &&defender.getCreaturesInPlay().stream().noneMatch(c->CombatUtil.canBlock(threat,c));
  }catch(RuntimeException unsupported){return false;}
 }
 public static List<SpellAbility> select(Player ai,List<SpellAbility> stock) {
  if(!GgsNinjutsuPolicy.enabled(ai)||Boolean.getBoolean("dragonmind.disableKaitoThreatPolicy")
    ||stock==null||stock.size()!=1||ai.getLife()<=0) return stock;
  var phase=ai.getGame().getPhaseHandler();SpellAbility draw=stock.get(0);
  if(!phase.isPlayerTurn(ai)||phase.getPhase()!=PhaseType.MAIN2
    ||draw.getApi()!=ApiType.Surveil||!draw.getHostCard().getName().equals("Kaito, Bane of Nightmares")
    ||draw.getHostCard().getController()!=ai) return stock;
  SpellAbility tap=draw.getHostCard().getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.Tap
    &&sa.getSubAbility()!=null&&sa.getSubAbility().getApi()==ApiType.PutCounter
    &&"Stun".equals(sa.getSubAbility().getParam("CounterType"))
    &&"2".equals(sa.getSubAbility().getParam("CounterNum"))).findFirst().orElse(null);
  if(tap==null)return stock;tap.setActivatingPlayer(ai);
  if(!tap.canPlay()||!ComputerUtilCost.canPayCost(tap,ai,false))return stock;
  for(Player opponent:ai.getOpponents()) {
   boolean regalia=opponent.getCardsIn(forge.game.zone.ZoneType.Battlefield).anyMatch(c->c.getName().equals("Brotherhood Regalia")&&!c.isEquipping()&&!c.isPhasedOut());
   boolean sword=opponent.getCardsIn(forge.game.zone.ZoneType.Battlefield).anyMatch(c->c.getName().equals("Vorpal Sword")&&!c.isEquipping()&&!c.isPhasedOut());
   if(!regalia||!sword)continue;
   for(Card threat:opponent.getCreaturesInPlay()) {
    if(threat.isTapped()||threat.isPhasedOut()||threat.hasSickness()||threat.hasKeyword(Keyword.DEFENDER)
      ||threat.hasKeyword(Keyword.WARD)||!tap.canTarget(threat)
      ||threat.getNetPower()+2<ai.getLife()
      ||!executableEquipmentLine(ai,threat))continue;
    tap.resetTargets();tap.getTargets().add(threat);return List.of(tap);
   }
  }
  return stock;
 }
}
