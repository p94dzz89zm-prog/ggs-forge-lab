import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

/** Add observers at original returns without changing the returned value. */
public final class ReservationProbeInstrumenter {
    public static void main(String[] args)throws Exception{
        ClassReader r=new ClassReader(Files.readAllBytes(Path.of(args[0])));ClassWriter w=new ClassWriter(r,ClassWriter.COMPUTE_MAXS);int[] matched={0,0};
        r.accept(new ClassVisitor(Opcodes.ASM8,w){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);
                boolean reserved=name.equals("isManaSourceReserved")&&desc.equals("(Lforge/game/player/Player;Lforge/game/card/Card;)Z");
                boolean paid=name.equals("payManaCost")&&desc.equals("(Lforge/game/mana/ManaCostBeingPaid;Lforge/game/spellability/SpellAbility;Lforge/game/player/Player;ZZZ)Ljava/util/List;");
                if(!reserved&&!paid)return mv;matched[reserved?0:1]++;
                return new MethodVisitor(Opcodes.ASM8,mv){public void visitInsn(int op){
                    if(reserved&&op==Opcodes.IRETURN){super.visitInsn(Opcodes.DUP);super.visitVarInsn(Opcodes.ALOAD,0);super.visitVarInsn(Opcodes.ALOAD,1);super.visitMethodInsn(Opcodes.INVOKESTATIC,"ReservationProbe","reserved","(ZLforge/game/player/Player;Lforge/game/card/Card;)V",false);}
                    if(paid&&op==Opcodes.ARETURN){super.visitInsn(Opcodes.DUP);super.visitVarInsn(Opcodes.ALOAD,2);super.visitVarInsn(Opcodes.ALOAD,1);super.visitMethodInsn(Opcodes.INVOKESTATIC,"ReservationProbe","paid","(Ljava/lang/Object;Lforge/game/player/Player;Lforge/game/spellability/SpellAbility;)V",false);}
                    super.visitInsn(op);
                }};
            }
        },0);
        if(matched[0]!=1||matched[1]!=1)throw new IllegalStateException("Expected exactly two diagnostic methods");
        Files.write(Path.of(args[1]),w.toByteArray(),StandardOpenOption.CREATE_NEW);System.out.println("PASS two return-value-preserving diagnostic hooks");
    }
}
