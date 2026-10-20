import forge.ai.bridge.DurableEvidence;
import com.google.gson.*;
import java.nio.file.*;

/** Executes production finalization with an evidence stream larger than the heap. */
public final class LargeEvidenceRegression {
 public static void main(String[] args)throws Exception {
  Path root=Path.of(args[0]);DurableEvidence.begin("large-stream");
  JsonObject row=new JsonObject();row.addProperty("payload","x".repeat(256*1024));String line=row.toString();
  for(int i=0;i<384;i++)DurableEvidence.append(root.resolve("audit/fixture/referee-events.jsonl"),line);
  JsonObject result=new JsonObject();result.addProperty("seed",93);result.addProperty("status","completed");
  DurableEvidence.finish(root.resolve("engine-records/fixture"),93,"fixture\nDragonMind Result: "+result+"\n",result);
  if(Files.size(root.resolve("audit/fixture/referee-events.jsonl"))<96L*1024*1024)throw new AssertionError("No large stream");
  System.out.println("PASS large durable evidence finalization under64MiB heap");
 }
}
