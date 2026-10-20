package forge.ai.bridge;
import com.google.gson.*;
import forge.game.Game;
/** Opt-in diagnostic only: no counters, choices, RNG or game objects are changed. */
public final class CardAllocationTrace {
 private CardAllocationTrace(){}
 public static synchronized void record(Game game,int id,String operation){
  if(!Boolean.getBoolean("forge.evidence.traceCardAllocation"))return;
  JsonObject row=new JsonObject();row.addProperty("kind","card_id_allocation_diagnostic");row.addProperty("operation",operation);row.addProperty("runtime_game_identity",System.identityHashCode(game));row.addProperty("id_or_counter",id);JsonArray frames=new JsonArray();for(StackTraceElement frame:Thread.currentThread().getStackTrace())if(frame.getClassName().startsWith("forge."))frames.add(frame.getClassName()+"."+frame.getMethodName()+":"+frame.getLineNumber());row.add("engine_frames",frames);System.err.println("DRAGONMIND_CARD_ALLOCATION "+row);
 }
}
