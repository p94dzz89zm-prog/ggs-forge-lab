import forge.deck.*;import forge.deck.io.DeckSerializer;import forge.model.FModel;import forge.gui.GuiBase;import forge.GuiDesktop;import java.io.File;
public class SlotDeckValidation {
 public static void main(String[] args){GuiBase.setInterface(new GuiDesktop());FModel.initialize(null,null);
 for(String path:args){Deck d=DeckSerializer.fromFile(new File(path));String problem=DeckFormat.Commander.getDeckConformanceProblem(d);int n=d.getMain().countAll()+d.getCommanders().size();
 System.out.println("DECK "+d.getName()+" total="+n+" commander="+d.getCommanders().size()+" problem="+problem);if(n!=100||problem!=null)throw new IllegalStateException(path+": "+problem);}
 System.exit(0);}
}
