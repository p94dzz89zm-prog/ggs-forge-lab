package forge.ai.ggs;
import com.google.gson.Gson;
import forge.ai.bridge.BridgeChannel;
import forge.game.player.Player;
import java.nio.file.Path;
import java.util.LinkedHashMap;
/** Private diagnostics distinct from real-game evaluations. */
public final class PlannerTrace {
 private PlannerTrace(){}
 public static void record(Player p,GgsLinePlanner.Review review,java.util.List<forge.game.spellability.SpellAbility> stock,java.util.List<forge.game.spellability.SpellAbility> selected,GgsProtectionReserve.Advice reserve) {
  String dir=System.getProperty("forge.audit.directory");if(dir==null)return;
  var row=new LinkedHashMap<String,Object>();row.put("kind","bounded_line_review");row.put("offline_private",true);
  row.put("player_id",p.getId());row.put("turn",p.getGame().getPhaseHandler().getTurn());
  row.put("assumptions","masked unknowns; line forecast excludes priority spells; separate scoped public-removal/March proof; stock combat; material heuristic; two-action beam; no learned probability");
  row.put("stock_actions",stock==null?java.util.List.of():stock.stream().map(Object::toString).toList());
  row.put("effective_actions",selected==null?java.util.List.of():selected.stream().map(Object::toString).toList());
  row.put("planner_applied",selected!=stock);
  row.put("protection_reservation",reserve);
  row.put("review",review);row.put("information",PlannerSnapshot.forPlayer(p));
  try{BridgeChannel.append(Path.of(dir,"planner-seat-"+p.getId()+".jsonl"),new Gson().toJson(row));}
  catch(java.io.IOException e){throw new IllegalStateException("Planner audit failure",e);}
 }
}
