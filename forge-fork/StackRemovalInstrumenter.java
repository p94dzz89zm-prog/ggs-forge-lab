import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

/** Suppress a removal notification only when no live/frozen instance existed. */
public final class StackRemovalInstrumenter {
    public static void main(String[] args) throws Exception {
        ClassReader r=new ClassReader(Files.readAllBytes(Path.of(args[0])));
        ClassWriter w=new ClassWriter(r,ClassWriter.COMPUTE_MAXS);int[] matched={0};
        r.accept(new ClassVisitor(Opcodes.ASM8,w){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);
                if(!name.equals("remove") || !desc.equals("(Lforge/game/spellability/SpellAbilityStackInstance;)V"))return mv;
                matched[0]++;
                return new MethodVisitor(Opcodes.ASM8,mv){
                    public void visitCode(){
                        super.visitCode();Label present=new Label();
                        super.visitVarInsn(Opcodes.ALOAD,0);super.visitFieldInsn(Opcodes.GETFIELD,"forge/game/zone/MagicStack","stack","Ljava/util/Deque;");super.visitVarInsn(Opcodes.ALOAD,1);
                        super.visitMethodInsn(Opcodes.INVOKEINTERFACE,"java/util/Deque","contains","(Ljava/lang/Object;)Z",true);super.visitJumpInsn(Opcodes.IFNE,present);
                        super.visitVarInsn(Opcodes.ALOAD,0);super.visitFieldInsn(Opcodes.GETFIELD,"forge/game/zone/MagicStack","frozenStack","Ljava/util/Stack;");super.visitVarInsn(Opcodes.ALOAD,1);
                        super.visitMethodInsn(Opcodes.INVOKEVIRTUAL,"java/util/Stack","contains","(Ljava/lang/Object;)Z",false);super.visitJumpInsn(Opcodes.IFNE,present);
                        super.visitInsn(Opcodes.RETURN);super.visitLabel(present);super.visitFrame(Opcodes.F_SAME,0,null,0,null);
                    }
                };
            }
        },0);
        if(matched[0]!=1)throw new IllegalStateException("Expected exactly one instance-removal method");
        Files.write(Path.of(args[1]),w.toByteArray(),StandardOpenOption.CREATE_NEW);System.out.println("PASS one generic stack-removal membership guard");
    }
}
