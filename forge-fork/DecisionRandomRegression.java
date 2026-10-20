import forge.ai.bridge.DecisionReplay;
import java.nio.file.*;
import java.security.*;
import java.util.*;

/** Focused RNG provider controls; not a game or complete replay certificate. */
public class DecisionRandomRegression {
 public static void main(String[] args)throws Exception {
  String mode=args[0];Path root=Path.of(args[1]);Files.createDirectories(root);
  String value=mode.equals("range")?"2147483648":"123";
  Path tape=root.resolve("random.jsonl");Files.writeString(tape,"{\"kind\":\"engine_random_bits\",\"index\":0,\"bits\":31,\"value\":"+value+"}\n{\"kind\":\"engine_random_complete\",\"requests\":1}\n",StandardOpenOption.CREATE_NEW);
  System.setProperty("forge.decision.replayTape","enabled-private-decision-input");System.setProperty("forge.decision.engineRandomTape",tape.toString());System.setProperty("forge.decision.engineRandomSha256",mode.equals("hash")?"0".repeat(64):HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(tape))));System.setProperty("forge.decision.replayDiagnostics",root.resolve("diagnostics").toString());
  try {
   int result=DecisionReplay.engineRandom(mode.equals("width")?32:31,999);
   if(!mode.equals("valid"))throw new AssertionError("Invalid RNG accepted");if(result!=123)throw new AssertionError("Generated value used instead of recorded engine request");
   try{DecisionReplay.engineRandom(31,999);throw new AssertionError("Exhausted engine RNG accepted");}catch(IllegalStateException expected){}
   System.out.println("PASS recorded engine RNG value used; exhaustion rejected");
  }catch(IllegalStateException expected){
   if(mode.equals("valid"))throw expected;String message=String.valueOf(expected.getCause());String fragment=mode.equals("hash")?"hash mismatch":mode.equals("width")?"request diverged":"out of range";if(!message.contains(fragment))throw expected;
   System.out.println("PASS engine RNG "+mode+" rejected");
  }
 }
}
