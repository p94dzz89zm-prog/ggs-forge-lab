import com.google.gson.*;
import forge.ai.bridge.DurableEvidence;
import java.nio.file.*;
import java.lang.reflect.Method;
import java.util.*;

/** Recorder-only microbenchmark, using a private frozen native row corpus. */
public class StructuredWriterBenchmark {
    static JsonObject attempt(String mode,Path root,List<JsonObject> rows,int repeats)throws Exception {
        Files.createDirectories(root);Method structured=mode.equals("structured")?
            DurableEvidence.class.getMethod("append",Path.class,JsonObject.class):null;
        DurableEvidence.begin("recorder-benchmark");Path file=root.resolve("audit/events.jsonl");
        long start=System.nanoTime();
        for(int r=0;r<repeats;r++)for(JsonObject row:rows){
            if(structured!=null)structured.invoke(null,file,row);
            else DurableEvidence.append(file,row.toString());
        }
        JsonObject result=new JsonObject();result.addProperty("status","completed_fixture");
        DurableEvidence.finish(root.resolve("results"),1,"recorder microbenchmark\n",result);
        long elapsed=System.nanoTime()-start;
        JsonObject report=new JsonObject();report.addProperty("mode",mode);report.addProperty("rows",rows.size()*repeats);
        report.addProperty("elapsed_nanos",elapsed);report.addProperty("bytes",Files.size(file));
        report.addProperty("sha256",DurableEvidence.hashFile(file));return report;
    }
    public static void main(String[] args)throws Exception {
        List<JsonObject> rows=new ArrayList<>();
        for(String line:Files.readAllLines(Path.of(args[2])))rows.add(JsonParser.parseString(line).getAsJsonObject());
        Path root=Path.of(args[1]);attempt(args[0],root.resolve("warmup"),rows,2);
        System.out.println(attempt(args[0],root.resolve("measured"),rows,16));
    }
}
