package forge.ai.ggs;

import forge.ai.*;
import forge.ai.simulation.GameCopier;
import forge.game.Game;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.*;

/** Preserve activation colors for a stock-chosen Whip cast, only after an
 * actual masked-copy cast/return succeeds. Does not select Whip or a deck swap.
 */
public final class GgsWhipManaPolicy {
 private GgsWhipManaPolicy(){}
 private static void drain(Game g){for(int n=0;n<32;n++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new IllegalStateException("resolution-cap");}
 private static boolean play(Player p,SpellAbility sa){sa.setActivatingPlayer(p);if(!sa.canPlay()||!ComputerUtilCost.canPayCost(sa,p,false)||!ComputerUtil.handlePlayingSpellAbility(p,sa,null))return false;drain(p.getGame());return true;}
 public static List<SpellAbility> select(Player live,List<SpellAbility> stock){
  if(PlannerContext.active()||!GgsNinjutsuPolicy.enabled(live)||Boolean.getBoolean("dragonmind.disableWhipManaPolicy")||stock==null||stock.size()!=1)return stock;
  SpellAbility cast=stock.get(0);Card whip=cast.getHostCard();
  if(!cast.isSpell()||!"Whip of Erebos".equals(whip.getName())||!whip.isInZone(ZoneType.Hand)||whip.getController()!=live)return stock;
  AiController controller=((PlayerControllerAi)live.getController()).getAi();
  if(!controller.getCardMemory().isMemorySetEmpty(AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL))return stock;
  List<Card> black=live.getLandsInPlay().stream().filter(c->"Swamp".equals(c.getName())&&!c.isTapped()&&!c.isPhasedOut()).limit(2).toList();
  if(black.size()!=2||live.getCardsIn(ZoneType.Graveyard).stream().noneMatch(Card::isCreature))return stock;
  long start=System.nanoTime();int index=whip.getSpellAbilities().indexOf(cast);if(index<0)return stock;
  boolean verified=false;
  try(PlannerContext ignored=PlannerContext.enter(181018)){
   GameCopier copier=new GameCopier(live.getGame());Game g=copier.makeCopy(null,live);Player p=copier.find(live);Card copy=copier.find(whip);AiController ai=((PlayerControllerAi)p.getController()).getAi();
   for(Card land:black)ai.getCardMemory().rememberCard(copier.find(land),AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);
   if(!play(p,copy.getSpellAbilities().get(index)))return stock;
   ai.getCardMemory().clearMemorySet(AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);
   Card resolved=p.getCardsIn(ZoneType.Battlefield).stream().filter(c->c.getId()==whip.getId()).findFirst().orElse(null);if(resolved==null)return stock;
   SpellAbility rise=resolved.getSpellAbilities().stream().filter(sa->sa.getApi()==ApiType.ChangeZone).findFirst().orElse(null);if(rise==null)return stock;rise.setActivatingPlayer(p);
   Card target=p.getCardsIn(ZoneType.Graveyard).stream().filter(Card::isCreature).filter(rise::canTarget).findFirst().orElse(null);if(target==null)return stock;
   rise.resetTargets();rise.getTargets().add(target);if(System.nanoTime()-start>1_000_000_000L)return stock;
   if(!play(p,rise))return stock;
   verified=p.getCardsIn(ZoneType.Battlefield).stream().anyMatch(c->c.getId()==target.getId())&&System.nanoTime()-start<=1_000_000_000L;
  }catch(RuntimeException unsupported){return stock;}
  if(verified)for(Card land:black)controller.getCardMemory().rememberCard(land,AiCardMemory.MemorySet.HELD_MANA_SOURCES_FOR_NEXT_SPELL);
  return stock;
 }
}
