import com.google.gson.*;
import forge.ai.AITest;
import forge.deck.*;
import forge.deck.io.DeckSerializer;
import java.nio.file.*;

/** Installed Forge Commander conformance only; independent Oracle review remains separate. */
public class DeckConformanceProbe extends AITest {
    public static void main(String[] args) throws Exception {
        DeckConformanceProbe t=new DeckConformanceProbe();t.initializeModel();
        JsonArray rows=new JsonArray();boolean passed=true;
        for(String name:args){
            Deck d=DeckSerializer.fromFile(Path.of(name).toFile());
            String issue=DeckFormat.Commander.getDeckConformanceProblem(d);
            boolean legal=DeckFormat.Commander.isLegalDeckPredicate().test(d);
            JsonObject row=new JsonObject();row.addProperty("file",name);row.addProperty("problem",issue);
            row.addProperty("engine_legal",legal);row.addProperty("main_count",d.getMain().countAll());
            row.addProperty("commander_count",d.get(DeckSection.Commander).countAll());rows.add(row);
            passed &= issue==null && legal;
        }
        System.out.println("DRAGONMIND_DECK_CONFORMANCE "+rows);
        if(!passed)throw new AssertionError("Archived deck fails installed Commander conformance");
        System.out.println("PASS installed Commander deck conformance; no independent Oracle/banlist certification");System.exit(0);
    }
}
