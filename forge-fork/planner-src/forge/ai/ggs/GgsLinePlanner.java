package forge.ai.ggs;

import forge.ai.ComputerUtil;
import forge.ai.ComputerUtilCard;
import forge.ai.ComputerUtilCost;
import forge.ai.simulation.GameCopier;
import forge.game.Game;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import java.util.*;

/** Experimental two-action, public-projection search. Not a win-probability model.
 * Branches pay costs and resolve effects in Forge. Combat uses stock attackers and
 * blockers with no priority spells. Unknown draws invalidate a branch. Never
 * called recursively, and never enabled by default. See LINE_PLANNER.md.
 */
public final class GgsLinePlanner {
 private GgsLinePlanner() {}
 public record Action(int cardId,int abilityIndex,String label) {}
 public record Line(List<Action> actions,double score,int life,int opponentLife,int creatures,int untappedLands) {}
 public record Review(String status,List<Line> lines,List<Action> chosen,int nodes,long elapsedMillis) {}
 private record Position(Game game,Player player) {}
 private static final class Search {
  final long start=System.nanoTime(),budget;int nodes;
  Search(long milliseconds){budget=milliseconds*1000000L;}
  void check(){if(System.nanoTime()-start>budget)throw new IllegalStateException("deadline");}
 }
 public static boolean eligible(Player p) {
  Game g=p.getGame();var h=g.getPhaseHandler();
  return !PlannerContext.active()&&!g.EXPERIMENTAL_RESTORE_SNAPSHOT&&h.isPlayerTurn(p)
   &&(h.getPhase()==PhaseType.MAIN1||h.getPhase()==PhaseType.MAIN2)&&g.getStack().isEmpty()
   &&g.getPlayers().size()==g.getMatch().getPlayers().size()
   &&!g.getCardsIn(ZoneType.Battlefield).anyMatch(Card::isFaceDown);
 }
 private static boolean supported(SpellAbility sa) {
  if(sa.getPayCosts()==null||sa.getPayCosts().getTotalMana().toString().contains("X"))return false;
  if(sa.usesTargeting()||sa.getSubAbility()!=null||sa.isLandAbility())return false;
  if(sa.isSpell())return sa.getApi()==ApiType.PermanentCreature||sa.getApi()==ApiType.PermanentNoncreature;
  return sa.isActivatedAbility()&&sa.getApi()==ApiType.PumpAll
   &&"Goro-Goro and Satoru".equals(sa.getHostCard().getName())
   &&"Creature.YouCtrl".equals(sa.getParam("ValidCards"))&&"Haste".equals(sa.getParam("KW"))
   &&!sa.hasParam("NumAtt")&&!sa.hasParam("NumDef");
 }
 private static List<Action> actions(Player p) {
  List<Action> result=new ArrayList<>();
  // Command-zone casting needs a separately verified command-tax copier; defer.
  List<Card> cards=new ArrayList<>();p.getCardsIn(ZoneType.Hand).forEach(cards::add);p.getCardsIn(ZoneType.Battlefield).forEach(cards::add);
  cards.sort(Comparator.comparingInt(Card::getId));
  for(Card c:cards)for(int i=0;i<c.getSpellAbilities().size();i++) {
   SpellAbility sa=c.getSpellAbilities().get(i);if(!supported(sa))continue;
   sa.setActivatingPlayer(p);
   if(sa.canPlay()&&ComputerUtilCost.canPayCost(sa,p,false)&&!GgsRecoveryPolicy.rejectRedundantHaste(p,sa))
    result.add(new Action(c.getId(),i,c.getName()+" / "+sa.getApi()));
  }
  if(result.size()>6)throw new IllegalStateException("action-cap");
  return result;
 }
 public static SpellAbility find(Player p,Action a) {
  for(Card c:p.getGame().getCardsInGame())if(c.getId()==a.cardId()&&a.abilityIndex()<c.getSpellAbilities().size())return c.getSpellAbilities().get(a.abilityIndex());
  return null;
 }
 private static Position copy(Player p) {
  GameCopier c=new GameCopier(p.getGame());Game g=c.makeCopy(null,p);return new Position(g,c.find(p));
 }
 private static void drain(Game g) {
  for(int n=0;n<64;n++) {
   g.getAction().checkStateEffects(true);g.getTriggerHandler().runWaitingTriggers();g.getStack().addAllTriggeredAbilitiesToStack();
   if(g.getStack().isEmpty())return;g.getStack().resolveStack();
  }
  throw new IllegalStateException("resolution-cap");
 }
 private static void execute(Position p,Action a) {
  SpellAbility sa=find(p.player(),a);if(sa==null)throw new IllegalStateException("missing-action");sa.setActivatingPlayer(p.player());
  if(!sa.canPlay()||!ComputerUtilCost.canPayCost(sa,p.player(),false)||!ComputerUtil.handlePlayingSpellAbility(p.player(),sa,null))throw new IllegalStateException("unpayable-action");
  drain(p.game());
 }
 private static Line evaluate(Position pos,List<Action> prefix,Search s) {
  s.check();Position forecast=copy(pos.player());Game g=forecast.game();Player p=forecast.player();
  if(g.getPhaseHandler().getPhase()==PhaseType.MAIN1) {
   // Common combat randomness: payment/trigger RNG consumed by one prefix must
   // not give that line a different random opponent assignment than another.
   try(PlannerContext combat=PlannerContext.enter(715518)) {
    g.getPhaseHandler().devAdvanceToPhase(PhaseType.MAIN2,()->drain(g));drain(g);
   }
  }
  for(Card c:p.getCardsIn(ZoneType.Hand))if(PlannerContext.UNKNOWN.equals(c.getName()))throw new IllegalStateException("unknown-draw");
  // Explicit material heuristic. Commander engines are ordinary board material;
  // no bonus for generating a trigger or merely activating the commander.
  double score=0;int otherLife=0,ownCreatures=p.getCreaturesInPlay().size();
  for(Player seat:g.getPlayers()) {
   double material=0;for(Card c:seat.getCardsIn(ZoneType.Battlefield))
    material+=c.isCreature()?ComputerUtilCard.evaluateCreature(c):c.isLand()?35:60+20*c.getCMC();
   double value=material+18*seat.getCardsIn(ZoneType.Hand).size()+4*seat.getLife();
   if(seat==p)score+=value;else{score-=value/Math.max(1,g.getPlayers().size()-1);otherLife+=seat.getLife();}
  }
  for(Player lost:g.getLostPlayers())if(lost!=p)score+=100000;
  if(p.getOutcome()!=null&&p.getOutcome().hasWon())score+=1000000;
  if(p.getLife()<=0||p.getOutcome()!=null&&p.getOutcome().lossState!=null)score-=1000000;
  int untapped=(int)p.getLandsInPlay().stream().filter(c->!c.isTapped()).count();score+=3*untapped;
  s.check();return new Line(List.copyOf(prefix),score,p.getLife(),otherLife,ownCreatures,untapped);
 }
 public static Review review(Player live,long budgetMillis) {
  long start=System.nanoTime();List<Line> lines=new ArrayList<>();Search s=new Search(budgetMillis);
  if(!eligible(live))return new Review("unsupported-position",List.of(),List.of(),0,0);
  try(PlannerContext ignored=PlannerContext.enter(715517)) {
   Position root=copy(live);List<Action> roots=actions(root.player());
   lines.add(evaluate(root,List.of(),s));
   List<Line> first=new ArrayList<>();
   for(Action a:roots) {
    s.check();Position branch=copy(root.player());execute(branch,a);s.nodes++;
    Line line=evaluate(branch,List.of(a),s);first.add(line);lines.add(line);
   }
   first.sort(Comparator.comparingDouble(Line::score).reversed());
   for(Line initial:first.subList(0,Math.min(2,first.size()))) {
    Position branch=copy(root.player());execute(branch,initial.actions().get(0));
    for(Action b:actions(branch.player())) {
     s.check();Position child=copy(branch.player());execute(child,b);s.nodes++;
     lines.add(evaluate(child,List.of(initial.actions().get(0),b),s));
    }
   }
   Line best=lines.stream().max(Comparator.comparingDouble(Line::score)).orElseThrow();
   return new Review("complete-bounded",List.copyOf(lines),best.actions(),s.nodes,(System.nanoTime()-start)/1000000);
  } catch(RuntimeException e) {
   return new Review("fallback:"+e.getClass().getSimpleName()+":"+e.getMessage(),List.copyOf(lines),List.of(),s.nodes,(System.nanoTime()-start)/1000000);
  }
 }
 /** Safe integration: unsupported stock actions and selected passes remain stock.
  * This prototype can reorder development; it cannot yet veto a stock cast. */
 public static List<SpellAbility> select(Player p,List<SpellAbility> stock) {
  if(!Boolean.getBoolean("dragonmind.linePlanner")||!GgsNinjutsuPolicy.enabled(p)||!eligible(p))return stock;
  if(stock!=null&&(stock.size()!=1||!supported(stock.get(0))))return stock;
  Review r=review(p,Long.getLong("dragonmind.linePlannerMillis",2000L));
  List<SpellAbility> selected=stock;
  if(r.status().equals("complete-bounded")&&!r.chosen().isEmpty()) {
   SpellAbility choice=find(p,r.chosen().get(0));
   if(choice!=null){choice.setActivatingPlayer(p);if(choice.canPlay()&&ComputerUtilCost.canPayCost(choice,p,false))selected=List.of(choice);}
  }
  PlannerTrace.record(p,r,stock,selected);return selected;
 }
}
