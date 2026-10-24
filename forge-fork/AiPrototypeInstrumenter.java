import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

/** Change only the AI prototype call and its scoped factory delegation. */
public final class AiPrototypeInstrumenter {
 public static void main(String[] args)throws Exception {
  String[] owners={"forge/ai/ability/TokenAi","forge/game/card/token/TokenInfo","forge/game/Game"};
  String proto="(Ljava/lang/String;Lforge/game/spellability/SpellAbility;Lforge/game/player/Player;)Lforge/game/card/Card;";
  String factory="(Lforge/item/IPaperCard;Lforge/game/player/Player;Lforge/game/Game;)Lforge/game/card/Card;";
  for(String owner:owners){
   Path input=Path.of(args[0]).resolve(owner+".class");
   ClassReader reader=new ClassReader(Files.readAllBytes(input));
   if(!reader.getClassName().equals(owner))throw new IllegalArgumentException("Wrong class: "+owner);
   ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_MAXS);int[] changes={0};
   reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
    public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] exceptions){
     MethodVisitor next=super.visitMethod(access,name,desc,sig,exceptions);
     if(owner.equals("forge/game/Game")&&(name.equals("nextCardId")||name.equals("nextHiddenCardId"))&&desc.equals("()I"))return new MethodVisitor(Opcodes.ASM8,next){
      public void visitInsn(int opcode){
       if(opcode==Opcodes.IRETURN){changes[0]++;super.visitInsn(Opcodes.DUP);super.visitMethodInsn(Opcodes.INVOKESTATIC,"forge/ai/bridge/AiTokenPrototypes","requireLiveIdRange","(I)V",false);}
       super.visitInsn(opcode);
      }
     };
     boolean ai=owner.endsWith("/TokenAi")&&name.equals("spawnToken")&&desc.equals("(Lforge/game/player/Player;Lforge/game/spellability/SpellAbility;)Lforge/game/card/Card;");
     boolean token=owner.endsWith("/TokenInfo")&&name.equals("getProtoType")&&desc.equals("(Ljava/lang/String;Lforge/game/spellability/SpellAbility;Lforge/game/player/Player;Z)Lforge/game/card/Card;");
     if(!ai&&!token)return next;
     return new MethodVisitor(Opcodes.ASM8,next){
      public void visitMethodInsn(int opcode,String calledOwner,String called,String descriptor,boolean itf){
       if(opcode==Opcodes.INVOKESTATIC&&ai&&calledOwner.equals("forge/game/card/token/TokenInfo")&&called.equals("getProtoType")&&descriptor.equals(proto)){
        changes[0]++;super.visitMethodInsn(opcode,"forge/ai/bridge/AiTokenPrototypes","getPrototype",descriptor,false);
       }else if(opcode==Opcodes.INVOKESTATIC&&token&&calledOwner.equals("forge/game/card/CardFactory")&&called.equals("getCard")&&descriptor.equals(factory)){
        changes[0]++;super.visitMethodInsn(opcode,"forge/ai/bridge/AiTokenPrototypes","createCard",descriptor,false);
       }else super.visitMethodInsn(opcode,calledOwner,called,descriptor,itf);
      }
     };
    }
   },0);
   int expected=owner.equals("forge/game/Game")?2:1;
   if(changes[0]!=expected)throw new IllegalStateException("Expected exactly"+expected+" changes in "+owner+", got "+changes[0]);
   Path output=Path.of(args[1]).resolve(owner+".class");Files.createDirectories(output.getParent());Files.write(output,writer.toByteArray());
   System.out.println("Scoped prototype delegation: "+owner);
  }
 }
}
