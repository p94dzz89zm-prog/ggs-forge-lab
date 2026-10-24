import com.google.gson.*;
import forge.ai.bridge.DurableEvidence;
import java.nio.file.*;

/** Synthetic valid-JSON compatibility, caller immutability and finite-number guard. */
public class StructuredWriterRegression {
    public static void main(String[] args)throws Exception {
        String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);
        DurableEvidence.begin("structured-writer-fixture");
        JsonObject row=JsonParser.parseString("{\"text\":\"quotes \\\" and \\n unicode α <>&\",\"numbers\":[1,-2,0.0,1e6],\"nested\":{\"yes\":true,\"nil\":null},\"stream_sequence\":99}").getAsJsonObject();
        String before=row.toString();Path path=root.resolve("audit/events.jsonl");
        if(mode.equals("nonfinite")){
            row.addProperty("bad",Double.NaN);
            try{DurableEvidence.append(path,row);throw new AssertionError("Nonfinite number accepted");}
            catch(java.io.IOException expected){if(!expected.getMessage().contains("Evidence append failed"))throw expected;}
            if(Files.exists(path)||Files.exists(path.resolveSibling("events.jsonl.receipt.json")))throw new AssertionError("Rejected stream was sealed");
            System.out.println("PASS structured nonfinite value rejected without completion");return;
        }
        for(int i=0;i<260;i++){
            if(mode.equals("string"))DurableEvidence.append(path,row.toString());else DurableEvidence.append(path,row);
            if(!before.equals(row.toString()))throw new AssertionError("Caller JSON mutated");
        }
        JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");
        DurableEvidence.finish(root.resolve("results"),9,"synthetic writer fixture\n",result);
        System.out.println("PASS writer compatibility fixture "+mode+" "+DurableEvidence.hashFile(path));
    }
}
