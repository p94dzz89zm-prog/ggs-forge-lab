import com.google.gson.*;
import forge.ai.bridge.DecisionReplay;
import java.lang.reflect.*;

/** Reject fractional/string/overflow choices instead of silently rounding them. */
public final class DecisionIntegerRegression {
 public static void main(String[] args)throws Exception {
  Method integer=DecisionReplay.class.getDeclaredMethod("integer",JsonElement.class);integer.setAccessible(true);
  if(!integer.invoke(null,JsonParser.parseString("7")).equals(7L))throw new AssertionError("Integer changed");
  for(String text:new String[]{"7.1","\"7\"","true","null","9223372036854775808"}){
   try{integer.invoke(null,JsonParser.parseString(text));throw new AssertionError("Invalid choice accepted: "+text);}
   catch(InvocationTargetException expected){if(!(expected.getCause() instanceof IllegalStateException))throw expected;}
  }
  System.out.println("PASS exact integer choice rejects fractional, quoted, boolean, null and overflowing values");
 }
}
