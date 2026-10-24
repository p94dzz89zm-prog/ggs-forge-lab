package forge.ai.ggs;

import forge.ai.ComputerUtil;
import forge.ai.ComputerUtilCost;
import forge.ai.simulation.GameCopier;
import forge.game.Game;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.*;

/** Bounded public-response proof, not a general threat probability model.
 * Only a single legal tap-to-destroy creature ability and ordinary X=1 March
 * are modeled. No opponent hand, anticipated draw, or card-rule edits.
 */
public final class GgsProtectionReserve {
 private GgsProtectionReserve(){}
 public record Advice(String status,Integer threatId,Integer protectorId,boolean veto,long elapsedMillis){}
 private record Position(Game game,Player player){}
 private record Threat(int cardId,int abilityIndex,int playerId){}
 private static Position copy(Player p){GameCopier c=new GameCopier(p.getGame());Game g=c.makeCopy(null,p);return new Position(g,c.find(p));}
 private static Card card(Game g,int id){for(Card c:g.getCardsIncludePhasingIn(ZoneType.Battlefield))if(c.getId()==id)return c;return null;}
 private static Card commander(Player p){for(Card c:p.getCardsIn(ZoneType.Battlefield))if(c.getController()==p&&"Goro-Goro and Satoru".equals(c.getName())&&!c.isPhasedOut())return c;return null;}
 private static Card march(Player p){for(Card c:p.getCardsIn(ZoneType.Hand))if("March of Swirling Mist".equals(c.getName()))return c;return null;}
 private static boolean otherBlue(Player p,Card march){return p.getCardsIn(ZoneType.Hand).anyMatch(c->c!=march&&c.isBlue());}
 private static boolean unknownDraw(Player p){return p.getCardsIn(ZoneType.Hand).anyMatch(c->PlannerContext.UNKNOWN.equals(c.getName()));}
 private static SpellAbility protection(Player p,Card target){
  Card c=march(p);if(c==null||target==null)return null;SpellAbility sa=c.getFirstSpellAbility();sa.setActivatingPlayer(p);sa.setXManaCostPaid(1);sa.resetTargets();sa.getTargets().add(target);return sa;
 }
 private static boolean payable(SpellAbility sa,Player p){return sa!=null&&sa.canPlay()&&sa.isTargetNumberValid()&&ComputerUtilCost.canPayCost(sa,p,false);}
 private static List<Threat> threats(Player p,Card target){
  List<Threat> out=new ArrayList<>();if(target==null)return out;
  for(Player enemy:p.getGame().getPlayers())if(enemy.isOpponentOf(p))for(Card c:enemy.getCardsIn(ZoneType.Battlefield)) {
   if(!c.isCreature()||c.isPhasedOut())continue;
   for(int i=0;i<c.getSpellAbilities().size();i++) {
    SpellAbility sa=c.getSpellAbilities().get(i);
    if(sa.getApi()!=ApiType.Destroy||!sa.isActivatedAbility()||sa.getSubAbility()!=null||!"T".equals(sa.getParam("Cost"))||sa.getMinTargets()!=1||sa.getMaxTargets()!=1)continue;
    sa.setActivatingPlayer(enemy);sa.resetTargets();sa.getTargets().add(target);
    if(sa.canTarget(target)&&payable(sa,enemy))out.add(new Threat(c.getId(),i,enemy.getId()));
   }
  }
  return out;
 }
 private static void drain(Game g){for(int n=0;n<64;n++){g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();if(g.getStack().isEmpty())return;g.getStack().resolveStack();}throw new IllegalStateException("resolution-cap");}
 private static boolean fire(Position pos,Threat t,boolean protect,int id){
  Card target=card(pos.game(),id),source=card(pos.game(),t.cardId());if(target==null||source==null||target.isPhasedOut())return false;
  Player enemy=pos.game().getPlayer(t.playerId());SpellAbility sa=source.getSpellAbilities().get(t.abilityIndex());sa.setActivatingPlayer(enemy);sa.resetTargets();sa.getTargets().add(target);
  if(!sa.canTarget(target)||!payable(sa,enemy)||!ComputerUtil.handlePlayingSpellAbility(enemy,sa,null))return false;
  if(protect){
   var picked=((forge.ai.PlayerControllerAi)pos.player().getController()).getAi().chooseSpellAbilityToPlay();
   if(picked==null||picked.size()!=1)return false;SpellAbility save=picked.get(0);
   if(!"March of Swirling Mist".equals(save.getHostCard().getName())||!save.getTargets().getTargetCards().contains(target)
      ||!payable(save,pos.player())||!save.canTarget(target)||!ComputerUtil.handlePlayingSpellAbility(pos.player(),save,null))return false;
  }
  drain(pos.game());return true;
 }
 private static Advice result(String status,Threat t,Card save,boolean veto,long start){return new Advice(status,t==null?null:t.cardId(),save==null?null:save.getId(),veto,(System.nanoTime()-start)/1000000);}
 private static void check(long start,long budget){if(System.nanoTime()-start>budget)throw new IllegalStateException("deadline");}
 public static Advice inspect(Player live,SpellAbility proposed,long milliseconds){
  long start=System.nanoTime(),budget=milliseconds*1000000L;Threat threat=null;Card save=null;
  if(Boolean.getBoolean("dragonmind.disableProtectionReserve"))return result("disabled",null,null,false,start);
  if(proposed==null||!GgsLinePlanner.eligible(live)||commander(live)==null||march(live)==null)return result("not-applicable",null,null,false,start);
  if(otherBlue(live,march(live)))return result("unsupported-alternate-exile-cost",null,null,false,start);
  int host=proposed.getHostCard().getId(),index=proposed.getHostCard().getSpellAbilities().indexOf(proposed);if(index<0)return result("unsupported-ability-copy",null,null,false,start);
  try(PlannerContext ignored=PlannerContext.enter(715521)){
   Position root=copy(live);Card leader=commander(root.player());save=march(root.player());int id=leader.getId();
   List<Threat> available=threats(root.player(),leader);if(available.size()!=1)return result(available.isEmpty()?"no-executable-public-removal":"unsupported-multiple-removals",null,save,false,start);
   threat=available.get(0);SpellAbility pre=protection(root.player(),leader);
   if(!payable(pre,root.player())||!pre.canTarget(leader))return result("protection-not-payable-before-action",threat,save,false,start);
   check(start,budget);
   Position after=copy(root.player());SpellAbility action=GgsLinePlanner.find(after.player(),new GgsLinePlanner.Action(host,index,"proposed"));if(action==null)throw new IllegalStateException("missing-action");action.setActivatingPlayer(after.player());
   if(!action.canPlay()||!ComputerUtilCost.canPayCost(action,after.player(),false)||!ComputerUtil.handlePlayingSpellAbility(after.player(),action,null))throw new IllegalStateException("action-payment-failed");drain(after.game());
   if(unknownDraw(after.player()))return result("unsupported-unknown-draw",threat,save,false,start);
   Card afterLeader=card(after.game(),id);if(afterLeader==null||afterLeader.isPhasedOut())return result("commander-not-exposed-after-action",threat,save,false,start);
   SpellAbility post=protection(after.player(),afterLeader);
   if(payable(post,after.player())&&post.canTarget(afterLeader))return result("protection-remains-payable",threat,save,false,start);
   check(start,budget);
   // Demonstrate the actual consequence after the proposed spend.
   if(!fire(after,threat,false,id)||card(after.game(),id)!=null)return result("removal-does-not-defeat-commander",threat,save,false,start);
   check(start,budget);
   // Demonstrate that retaining the current resources really saves it.
   Position held=copy(root.player());if(!fire(held,threat,true,id))return result("protection-response-unverified",threat,save,false,start);
   Card retained=card(held.game(),id);check(start,budget);
   if(retained!=null&&retained.isPhasedOut())return result("reserve-March-against-public-removal",threat,save,true,start);
   return result("protection-did-not-preserve-commander",threat,save,false,start);
  }catch(RuntimeException e){return result("fallback:"+e.getClass().getSimpleName()+":"+e.getMessage(),threat,save,false,start);}
 }
}
