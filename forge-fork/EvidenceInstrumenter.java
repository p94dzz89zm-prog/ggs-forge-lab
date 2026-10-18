import java.nio.file.*;
import java.util.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;

/** Offline injection only: gameplay needs no JDK-internal exports or agent. */
public final class EvidenceInstrumenter {
 static boolean selected(String owner,String name,String desc,int access) {
  if((access&(Opcodes.ACC_ABSTRACT|Opcodes.ACC_NATIVE|Opcodes.ACC_SYNTHETIC))!=0||name.startsWith("<"))return false;
  if(owner.startsWith("forge/game/ability/effects/"))return name.equals("resolve");
  if(owner.equals("forge/game/zone/MagicStack"))return Set.of("add","resolveStack","addAllTriggeredAbilitiesToStack").contains(name);
  if(owner.equals("forge/game/Game"))return name.equals("fireEvent");
  if(owner.equals("forge/game/GameAction"))return name.equals("reveal")&&Type.getArgumentTypes(desc).length==6||name.equals("revealTo")&&Type.getArgumentTypes(desc).length==4;
  if(owner.equals("forge/game/mana/ManaPool"))return Set.of("addMana","addManaNoEvent","tryPayCostWithMana","clearPool","refundManaPaid").contains(name)&&!desc.startsWith("([");
  if(owner.equals("forge/game/cost/CostPayment"))return Set.of("payCost","payComputerCosts","refundPayment").contains(name);
  if(owner.equals("forge/game/cost/CostAdjustment"))return name.equals("adjust");
  if(owner.startsWith("forge/game/cost/Cost"))return name.equals("payAsDecided");
  if(owner.equals("forge/ai/ComputerUtilMana"))return name.equals("payManaCost")&&desc.startsWith("(Lforge/game/mana/ManaCostBeingPaid;Lforge/game/spellability/SpellAbility;Lforge/game/player/Player;ZZZ)");
  if(owner.equals("forge/ai/PlayerControllerAi")||owner.equals("forge/ai/bridge/PlayerControllerBridge")||owner.equals("forge/game/player/PlayerController"))return name.equals("reveal")||name.equals("tempShowCards")||name.equals("endTempShowCards")||name.startsWith("choose")||name.startsWith("confirm")||name.startsWith("order")||name.startsWith("declare")||name.startsWith("assign")||name.startsWith("arrange")||Set.of("getAbilityToPlay","payManaCost","playSpellAbilityForFree","playSaFromPlayEffect","mulliganKeepHand").contains(name);
  return false;
 }
 public static void main(String[] args)throws Exception {
  Path source=Path.of(args[0]),dest=Path.of(args[1]);List<String> inventory=new ArrayList<>();
  try(var walk=Files.walk(source)) {for(Path file:walk.filter(p->p.toString().endsWith(".class")).toList()) {
   byte[] bytes=Files.readAllBytes(file);ClassReader reader=new ClassReader(bytes);String owner=reader.getClassName();
   ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_FRAMES | ClassWriter.COMPUTE_MAXS) {
    protected ClassLoader getClassLoader(){return EvidenceInstrumenter.class.getClassLoader();}
   };boolean[] changed={false};
   reader.accept(new ClassVisitor(Opcodes.ASM8,writer) {
    public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] exceptions) {
     MethodVisitor mv=super.visitMethod(access,name,desc,sig,exceptions);
     if(!selected(owner,name,desc,access))return mv;
     changed[0]=true;inventory.add(owner+"."+name+desc);
     return new AdviceAdapter(Opcodes.ASM8,mv,access,name,desc) {
      int token;
      protected void onMethodEnter() {
       push(owner+"."+name+desc);if((access&Opcodes.ACC_STATIC)==0)loadThis();else visitInsn(ACONST_NULL);loadArgArray();
       invokeStatic(Type.getObjectType("forge/ai/bridge/EngineEvidence"),new Method("enter","(Ljava/lang/String;Ljava/lang/Object;[Ljava/lang/Object;)J"));token=newLocal(Type.LONG_TYPE);storeLocal(token);
      }
      protected void onMethodExit(int opcode) {
       // Original exceptions are retained as incomplete calls; no fake success.
       if(opcode==ATHROW)return;
       Type ret=Type.getReturnType(desc);int result=-1;
       if(opcode!=RETURN){result=newLocal(ret);storeLocal(result);}
       loadLocal(token);if(opcode==RETURN)visitInsn(ACONST_NULL);else {loadLocal(result);box(ret);}
       invokeStatic(Type.getObjectType("forge/ai/bridge/EngineEvidence"),new Method("leave","(JLjava/lang/Object;)V"));
       if(opcode!=RETURN)loadLocal(result);
      }
     };
    }
   },ClassReader.EXPAND_FRAMES);
   if(changed[0]){Path out=dest.resolve(source.relativize(file));Files.createDirectories(out.getParent());Files.write(out,writer.toByteArray());}
  }}
  Collections.sort(inventory);Files.write(dest.resolve("instrumented-methods.txt"),inventory);
  for(String required:List.of("forge/game/Game.fireEvent","forge/game/GameAction.reveal(","forge/game/GameAction.revealTo(","forge/game/mana/ManaPool.tryPayCostWithMana","forge/game/cost/CostPayment.payComputerCosts","forge/ai/ComputerUtilMana.payManaCost"))if(inventory.stream().noneMatch(s->s.startsWith(required)))throw new IllegalStateException("Missing required hook: "+required);
  System.out.println("Instrumented methods: "+inventory.size());
 }
}
