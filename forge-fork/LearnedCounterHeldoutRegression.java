import com.google.gson.*;
import forge.ai.*;
import forge.deck.Deck;
import forge.game.*;
import forge.game.phase.PhaseType;
import forge.game.player.*;
import java.util.*;

/** Frozen unseen-card local-resource diagnostics. Never training or full games.
 * Four-player positions are explicit scope controls: v1 must retain stock.
 */
public class LearnedCounterHeldoutRegression extends LearnedCounterPreferenceRegression {
 int players=3;
 @Override protected Game initAndCreateThreePlayerGame() {
  if(players==3)return super.initAndCreateThreePlayerGame();
  initAndCreateGame(); // Install the same test model/services as AITest.
  List<RegisteredPlayer> seats=new ArrayList<>();
  for(String name:List.of("opponent","ai","remover","fourth"))
   seats.add(new RegisteredPlayer(new Deck()).setPlayer(new LobbyPlayerAi(name,null)));
  GameRules rules=new GameRules(GameType.Constructed);
  Game g=new Game(seats,rules,new Match(rules,seats,"Heldout four-player diagnostic"));
  g.setAge(GameStage.Play);g.getPhaseHandler().devModeSet(PhaseType.MAIN1,g.getPlayers().get(1));
  g.getPhaseHandler().onStackResolved();return g;
 }
 public static void main(String[] args) {
  LearnedCounterHeldoutRegression t=new LearnedCounterHeldoutRegression();t.initializeModel();
  t.players=Integer.parseInt(args[0]);if(t.players!=3&&t.players!=4)throw new IllegalArgumentException("3 or 4 players required");
  boolean learned=args[1].equals("learned");
  List<String> cards=List.of("Grizzly Bears","Runeclaw Bear","Centaur Courser","Nessian Courser",
   "Craw Wurm","Colossal Dreadmaw","Air Elemental","Wind Drake","Coral Merfolk",
   "Walking Corpse","Goblin Piker","Silvercoat Lion");
  for(int i=0;i<cards.size();i++)for(boolean own:List.of(false,true)) {
   long seed=2026120210L+i;int life=30+new Random(seed).nextInt(11);
   forge.util.MyRandom.setRandom(new Random(seed));
   Outcome actual=t.play(cards.get(i),own,null,learned&&t.players==3,life);
   JsonObject row=new JsonObject();row.addProperty("purpose","heldout_evaluation");
   row.addProperty("card",cards.get(i));row.addProperty("own",own);row.addProperty("seed",seed);
   row.addProperty("players",t.players);row.addProperty("life",life);row.addProperty("preferred_counter",own);
   row.addProperty("model_enabled",learned);row.addProperty("agreement",actual.targetSurvives()==own);
   row.add("actual",new Gson().toJsonTree(actual));
   if(!learned&&t.players==3) {
    forge.util.MyRandom.setRandom(new Random(seed));row.add("counter_branch",new Gson().toJsonTree(t.play(cards.get(i),own,true,false,life)));
    forge.util.MyRandom.setRandom(new Random(seed));row.add("pass_branch",new Gson().toJsonTree(t.play(cards.get(i),own,false,false,life)));
   }
   System.out.println("HELDOUT_DECISION "+row);
  }
  System.out.println("Checks passed: "+t.checks);System.exit(0);
 }
}
