import java.nio.file.*;
import java.util.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;
/** Observe allocation returns and post-sync counters; default behavior unchanged. */
public final class CardAllocationTraceInstrumenter {
 public static void main(String[] args)throws Exception {
  ClassReader reader=new ClassReader(Files.readAllBytes(Path.of(args[0])));if(!reader.getClassName().equals("forge/game/Game"))throw new IllegalArgumentException("Game class required");List<String> hooks=new ArrayList<>();ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_MAXS);
  reader.accept(new ClassVisitor(Opcodes.ASM8,writer){public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] exceptions){MethodVisitor method=super.visitMethod(access,name,desc,sig,exceptions);boolean allocate=name.equals("nextCardId")&&desc.equals("()I"),sync=name.equals("dangerouslySyncCardIdCounters")&&desc.equals("(Lforge/game/Game;)V");if(!allocate&&!sync)return method;hooks.add(name+desc);return new AdviceAdapter(Opcodes.ASM8,method,access,name,desc){protected void onMethodExit(int opcode){if(opcode==ATHROW)return;if(allocate){dup();loadThis();swap();push("nextCardId_return");invokeStatic(Type.getObjectType("forge/ai/bridge/CardAllocationTrace"),new Method("record","(Lforge/game/Game;ILjava/lang/String;)V"));}else{loadThis();loadThis();getField(Type.getObjectType("forge/game/Game"),"cardIdCounter",Type.INT_TYPE);push("sync_receiver_after");invokeStatic(Type.getObjectType("forge/ai/bridge/CardAllocationTrace"),new Method("record","(Lforge/game/Game;ILjava/lang/String;)V"));loadArg(0);loadArg(0);getField(Type.getObjectType("forge/game/Game"),"cardIdCounter",Type.INT_TYPE);push("sync_argument_after");invokeStatic(Type.getObjectType("forge/ai/bridge/CardAllocationTrace"),new Method("record","(Lforge/game/Game;ILjava/lang/String;)V"));}}};}},ClassReader.EXPAND_FRAMES);
  if(hooks.size()!=2)throw new IllegalStateException("Exact2 allocation hooks required: "+hooks);Files.write(Path.of(args[1]),writer.toByteArray());System.out.println("Observed allocation hooks: "+hooks);
 }
}
