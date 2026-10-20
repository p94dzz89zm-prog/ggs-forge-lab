import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;

/** Evidence-only injection into the exact frozen PhaseHandler class. */
public class ReadinessInstrumenter {
 public static void main(String[] args) throws Exception {
  ClassReader r=new ClassReader(Files.readAllBytes(Path.of(args[0])));
  ClassWriter w=new ClassWriter(r,ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS);
  int[] hooks={0,0,0,0};
  r.accept(new ClassVisitor(Opcodes.ASM8,w){
   public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] exceptions){
    MethodVisitor mv=super.visitMethod(access,name,desc,sig,exceptions);
    if(!name.equals("checkStateBasedEffects")&&!name.equals("mainLoopStep")&&!name.equals("mainGameLoop"))return mv;
    return new AdviceAdapter(Opcodes.ASM8,mv,access,name,desc){
     Type game=Type.getObjectType("forge/game/Game"), owner=Type.getObjectType("forge/game/phase/PhaseHandler"), trace=Type.getObjectType("forge/ai/bridge/ReadinessTrace");
     void game(){loadThis();getField(owner,"game",game);}
     void event(String kind,boolean resultOnStack){
      int result=-1;
      if(resultOnStack){dup();result=newLocal(Type.BOOLEAN_TYPE);storeLocal(result);}
      game();push(kind);if(resultOnStack)loadLocal(result);else push(false);
      invokeStatic(trace,new Method("event","(Lforge/game/Game;Ljava/lang/String;Z)V"));
     }
     protected void onMethodEnter(){
      if(name.equals("mainGameLoop")){game();invokeStatic(trace,new Method("begin","(Lforge/game/Game;)V"));hooks[3]++;}
      if(name.equals("checkStateBasedEffects")){event("readiness_enter",false);hooks[0]++;}
     }
     public void visitMethodInsn(int opcode,String target,String method,String signature,boolean itf){
      if(name.equals("mainLoopStep")&&target.equals("forge/game/player/PlayerController")&&method.equals("chooseSpellAbilityToPlay")){event("priority_offer",false);hooks[2]++;}
      super.visitMethodInsn(opcode,target,method,signature,itf);
      if(name.equals("checkStateBasedEffects")&&method.equals("checkStateEffects")&&signature.endsWith(")Z")){event("sba_return",true);hooks[1]++;}
      if(name.equals("checkStateBasedEffects")&&method.equals("addAllTriggeredAbilitiesToStack")&&signature.equals("()Z")){event("triggers_return",true);hooks[1]++;}
     }
     protected void onMethodExit(int opcode){
      if(opcode==ATHROW)return; // Never manufacture a successful terminal record.
      if(name.equals("checkStateBasedEffects"))event("readiness_exit",true);
      if(name.equals("mainGameLoop")){game();invokeStatic(trace,new Method("finish","(Lforge/game/Game;)V"));}
     }
    };
   }
  },ClassReader.EXPAND_FRAMES);
  if(hooks[0]!=1||hooks[1]!=2||hooks[2]!=1||hooks[3]!=1)throw new IllegalStateException("Unexpected native readiness call graph: "+java.util.Arrays.toString(hooks));
  Files.write(Path.of(args[1]),w.toByteArray(),StandardOpenOption.CREATE_NEW);
  System.out.println("PASS readiness instrumentation call graph "+java.util.Arrays.toString(hooks));
 }
}
