import forge.ai.AITest;
import forge.deck.*;
import forge.deck.io.DeckSerializer;
import java.io.File;
public class PureDeckValidation extends AITest {
 public static void main(String[] args){PureDeckValidation t=new PureDeckValidation();t.initializeModel();
 for(String file:args){Deck d=DeckSerializer.fromFile(new File(file));String problem=DeckFormat.Commander.getDeckConformanceProblem(d);
 int n=d.getMain().countAll()+d.getCommanders().size();
 System.out.println("DECK "+d.getName()+" total="+n+" commander="+d.getCommanders().size()+" problem="+problem);
 if(n!=100||problem!=null)throw new IllegalStateException(file+": "+problem);
 }System.exit(0);}
}
