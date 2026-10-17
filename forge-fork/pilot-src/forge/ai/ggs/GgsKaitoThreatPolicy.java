package forge.ai.ggs;

import forge.ai.ComputerUtilCost;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.util.List;

/** Narrow public-state survival guard, not a general future-combat solver.
 * Before Kaito draws in MAIN2, stop a creature that can become lethal with
 * the opponent's visible, currently unattached Regalia and Vorpal Sword.
 * Only untapped ordinary Swamps certify the combined equip payment. Other
 * mana sources, attached/warded targets and unknown interaction stay stock.
 */
public final class GgsKaitoThreatPolicy {
 private GgsKaitoThreatPolicy() {}
 private static boolean equipmentCanTarget(Player owner,String name,Card threat) {
  for(Card equipment:owner.getCardsIn(forge.game.zone.ZoneType.Battlefield)) {
   if(!equipment.getName().equals(name)||equipment.isEquipping()||equipment.isPhasedOut())continue;
   for(SpellAbility equip:equipment.getSpellAbilities()) {
    equip.setActivatingPlayer(owner);
    if(equip.getApi()==ApiType.Attach&&equip.canTarget(threat))return true;
   }
  }
  return false;
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
   long swamps=opponent.getLandsInPlay().stream().filter(c->c.getName().equals("Swamp")&&!c.isTapped()&&!c.isPhasedOut()).count();
   for(Card threat:opponent.getCreaturesInPlay()) {
    if(threat.isTapped()||threat.isPhasedOut()||threat.hasSickness()||threat.hasKeyword(Keyword.DEFENDER)
      ||threat.hasKeyword(Keyword.WARD)||!tap.canTarget(threat)
      ||threat.getNetPower()+2<ai.getLife()||swamps<(threat.getType().isLegendary()?3:5)
      ||!equipmentCanTarget(opponent,"Brotherhood Regalia",threat)
      ||!equipmentCanTarget(opponent,"Vorpal Sword",threat))continue;
    tap.resetTargets();tap.getTargets().add(threat);return List.of(tap);
   }
  }
  return stock;
 }
}
