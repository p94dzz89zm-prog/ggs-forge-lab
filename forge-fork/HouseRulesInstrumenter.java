import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

/** Narrow default-off rules-variant hooks; protected historical JAR is immutable. */
public final class HouseRulesInstrumenter {
    static final String HOUSE="forge/game/mulligan/CommanderHouseRules";
    public static void main(String[] args) throws Exception {
        ClassReader reader=new ClassReader(Files.readAllBytes(Path.of(args[0])));
        ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_MAXS);
        int[] hooks={0};String owner=reader.getClassName();
        reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);
                return new MethodVisitor(Opcodes.ASM8,mv){
                    public void visitInsn(int opcode){
                        if(owner.equals("forge/game/player/RegisteredPlayer") && name.equals("getStartingLife") && desc.equals("()I") && opcode==Opcodes.IRETURN){
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,HOUSE,"startingLife","(I)I",false);hooks[0]++;
                        }
                        super.visitInsn(opcode);
                    }
                    public void visitMethodInsn(int op,String target,String method,String descriptor,boolean itf){
                        if(owner.equals("forge/game/player/Player") && name.equals("checkLoseCondition") && target.equals(owner) && method.equals("getCommanderDamage") && descriptor.equals("()Ljava/lang/Iterable;")){
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,HOUSE,"damageForLoss","(Lforge/game/player/Player;)Ljava/lang/Iterable;",false);hooks[0]++;return;
                        }
                        super.visitMethodInsn(op,target,method,descriptor,itf);
                        if(owner.equals("forge/game/mulligan/MulliganService") && name.equals("initializeMulligans") && method.equals("<init>") && target.startsWith("forge/game/mulligan/") && descriptor.equals("(Lforge/game/player/Player;Z)V")){
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,HOUSE,"mulligan","(Lforge/game/mulligan/AbstractMulligan;)Lforge/game/mulligan/AbstractMulligan;",false);hooks[0]++;
                        }
                    }
                };
            }
        },0);
        int expected=owner.equals("forge/game/mulligan/MulliganService")?6:1;
        if(hooks[0]!=expected)throw new IllegalStateException("Unexpected house hook count "+owner+":"+hooks[0]);
        Files.write(Path.of(args[1]),writer.toByteArray(),StandardOpenOption.CREATE_NEW);
        System.out.println("PASS house hooks "+owner+":"+hooks[0]);
    }
}
