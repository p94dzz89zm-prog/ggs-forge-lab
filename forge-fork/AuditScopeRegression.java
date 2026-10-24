import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.player.*;
import com.google.gson.*;
import org.testng.Assert;
import java.nio.file.*;

public class AuditScopeRegression extends AITest {
 public static void main(String[]args)throws Exception {
  AuditScopeRegression t=new AuditScopeRegression();t.initializeModel();Game g=t.initAndCreateGame();
  Player selected=g.getPlayers().get(1),other=g.getPlayers().get(0);Path dir=Files.createTempDirectory("audit-scope");
  System.setProperty("forge.audit.directory",dir.toString());System.setProperty("forge.audit.player",selected.getName());
  var audit=PlayerControllerBridge.class.getDeclaredMethod("audit",String.class,JsonObject.class);audit.setAccessible(true);
  for(Player player:g.getPlayers()){
   PlayerControllerBridge controller=new PlayerControllerBridge(g,player,new LobbyPlayerAi(player.getName(),null));
   audit.invoke(controller,"scope-test",new JsonObject());
   BridgeAudit.evaluation(player,t.addCard("Runeclaw Bear",player).getFirstSpellAbility(),"scope-test");
  }
  Assert.assertTrue(Files.exists(dir.resolve("seat-"+selected.getId()+".jsonl")));System.out.println("PASS selected snapshot preserved");
  Assert.assertFalse(Files.exists(dir.resolve("seat-"+other.getId()+".jsonl")));System.out.println("PASS unselected snapshot skipped");
  Assert.assertTrue(Files.exists(dir.resolve("evaluation-seat-"+selected.getId()+".jsonl")));Assert.assertFalse(Files.exists(dir.resolve("evaluation-seat-"+other.getId()+".jsonl")));System.out.println("PASS evaluation scope preserved");
  System.clearProperty("forge.audit.player");
  audit.invoke(new PlayerControllerBridge(g,other,new LobbyPlayerAi(other.getName(),null)),"scope-test",new JsonObject());
  Assert.assertTrue(Files.exists(dir.resolve("seat-"+other.getId()+".jsonl")));System.out.println("PASS default all-seat audit preserved");
  System.out.println("Checks passed: 4");System.exit(0);
 }
}
