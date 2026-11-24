import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

public final class Install {
    public static void main(String[] args) throws Exception {
        ClassReader reader = new ClassReader(Files.readAllBytes(Path.of(args[0])));
        ClassWriter writer = new ClassWriter(reader, 0);
        int[] matches = {0};
        reader.accept(new ClassVisitor(Opcodes.ASM8, writer) {
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex) {
                return new MethodVisitor(Opcodes.ASM8, super.visitMethod(access,name,desc,sig,ex)) {
                    public void visitMethodInsn(int op,String owner,String method,String descriptor,boolean itf) {
                        if (name.equals("mulliganKeepHand") && desc.equals("(Lforge/game/player/Player;I)Z")
                                && op == Opcodes.INVOKESTATIC && owner.equals("forge/ai/validation/SharedOpening")
                                && method.equals("wantMulligan") && descriptor.equals("(Lforge/game/player/Player;I)Z")) {
                            owner = "forge/ai/validation/IndependentOpening";
                            matches[0]++;
                        }
                        super.visitMethodInsn(op,owner,method,descriptor,itf);
                    }
                };
            }
        }, 0);
        if (matches[0] != 1) throw new IllegalStateException("Unexpected callback count");
        Files.write(Path.of(args[1]), writer.toByteArray(), StandardOpenOption.CREATE_NEW);
    }
}
