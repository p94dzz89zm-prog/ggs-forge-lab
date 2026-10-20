import forge.ai.bridge.DurableEvidence;
import com.google.gson.*;
import java.nio.file.*;
/** Executes the exact production writer, including an abrupt interrupted process. */
public class DurableEvidenceRegression {
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[1]);DurableEvidence.begin("fixture-game");
  for(int seat=0;seat<4;seat++)for(int n=0;n<3;n++){
   JsonObject row=new JsonObject(),state=new JsonObject();state.addProperty("viewer_id",seat);JsonArray ps=new JsonArray();
   for(int id=0;id<4;id++){JsonObject p=new JsonObject();p.addProperty("id",id);p.add("battlefield",new JsonArray());if(id==seat)p.add("hand",new JsonArray());ps.add(p);}state.add("players",ps);row.add("state",state);
   DurableEvidence.append(root.resolve("audit/fixture/seat-"+seat+".jsonl"),row.toString());
  }
  if(args[0].equals("interrupt"))Runtime.getRuntime().halt(17);
  JsonObject result=new JsonObject();result.addProperty("seed",73);result.addProperty("status","completed");
  DurableEvidence.finish(root.resolve("engine-records/fixture"),73,"event\nDragonMind Result: "+result+"\n",result);
  boolean blocked=false;try{DurableEvidence.append(root.resolve("audit/fixture/seat-0.jsonl"),"{}");}catch(java.io.IOException e){blocked=true;}
  if(!blocked)throw new AssertionError("Write accepted after seal");
  System.out.println("PASS durable writer finalization and post-seal rejection");
 }
}
