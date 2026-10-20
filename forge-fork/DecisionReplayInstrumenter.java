import java.nio.file.*;
import java.util.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;

/** Inject before existing evidence hooks. No replay property means original code.
 * Every instrumented controller choice is intercepted; unsupported hooks throw.
 */
public final class DecisionReplayInstrumenter {
 public static void main(String[] args)throws Exception {
  Path source=Path.of(args[0]),dest=Path.of(args[1]);List<String> inventory=new ArrayList<>();
  try(var files=Files.walk(source)){for(Path file:files.filter(p->p.toString().endsWith(".class")).toList()) {
   ClassReader reader=new ClassReader(Files.readAllBytes(file));String owner=reader.getClassName();
   ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){
    protected ClassLoader getClassLoader(){return DecisionReplayInstrumenter.class.getClassLoader();}
   };
   reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
    public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] exceptions) {
     MethodVisitor method=super.visitMethod(access,name,desc,sig,exceptions);
     if(!EvidenceInstrumenter.selected(owner,name,desc,access)||Set.of("reveal","tempShowCards","endTempShowCards").contains(name))return method;
     String hook=owner+"."+name+desc;inventory.add(hook);
     return new AdviceAdapter(Opcodes.ASM8,method,access,name,desc){
      protected void onMethodEnter(){
       invokeStatic(Type.getObjectType("forge/ai/bridge/DecisionReplay"),new Method("enabled","()Z"));Label original=newLabel();ifZCmp(EQ,original);
       push(hook);loadThis();loadArgArray();invokeStatic(Type.getObjectType("forge/ai/bridge/DecisionReplay"),new Method("invoke","(Ljava/lang/String;Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;"));
       Type result=Type.getReturnType(desc);if(result.equals(Type.VOID_TYPE))pop();else unbox(result);returnValue();mark(original);
      }
     };
    }
   },ClassReader.EXPAND_FRAMES);
   Path output=dest.resolve(source.relativize(file));Files.createDirectories(output.getParent());Files.write(output,writer.toByteArray());
  }}
  Collections.sort(inventory);Files.write(dest.resolve("decision-hooks.txt"),inventory);System.out.println("Fail-closed controller hooks: "+inventory.size());
 }
}
