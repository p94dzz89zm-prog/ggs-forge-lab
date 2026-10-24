import java.nio.file.*;
import java.util.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.tree.*;

/** Replace one known sequential round; preserve every other method. */
public final class MulliganRoundInstrumenter {
    static byte[] methodBytes(MethodNode method) {
        ClassWriter out = new ClassWriter(0);
        out.visit(Opcodes.V17, Opcodes.ACC_PUBLIC, "MethodFingerprint", null, "java/lang/Object", null);
        method.accept(out); out.visitEnd(); return out.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        ClassNode node = new ClassNode(Opcodes.ASM8);
        new ClassReader(Files.readAllBytes(Path.of(args[0]))).accept(node, 0);
        boolean london = node.name.equals("forge/game/mulligan/LondonMulligan");
        if (!london && !node.name.equals("forge/game/mulligan/MulliganService")) throw new IllegalArgumentException("Wrong class");
        String targetName = london ? "canMulligan" : "runPlayerMulligans";
        String targetDesc = london ? "()Z" : "()V";
        Map<String, byte[]> untouched = new TreeMap<>();
        MethodNode target = null;
        for (MethodNode m : node.methods) {
            if (m.name.equals(targetName) && m.desc.equals(targetDesc)) {
                if (target != null) throw new IllegalStateException("Duplicate method");
                target = m;
            } else untouched.put(m.name + m.desc, methodBytes(m));
        }
        if (target == null) throw new IllegalStateException("Missing round method");
        Map<String, Integer> calls = new TreeMap<>();
        for (AbstractInsnNode insn : target.instructions) if (insn instanceof MethodInsnNode) {
            MethodInsnNode m = (MethodInsnNode) insn;
            calls.merge(m.owner + "." + m.name + m.desc, 1, Integer::sum);
        }
        for (String key : london ? new String[]{
            "forge/game/mulligan/LondonMulligan.tuckCardsDuringMulligan()I",
            "forge/game/player/Player.getMaxHandSize()I"} : new String[]{
            "forge/game/player/PlayerController.mulliganKeepHand(Lforge/game/player/Player;I)Z",
            "forge/game/mulligan/AbstractMulligan.mulligan()V",
            "forge/game/mulligan/AbstractMulligan.keep()V"})
            if (!Integer.valueOf(1).equals(calls.get(key))) throw new IllegalStateException("Unknown round shape: " + key);
        target.instructions.clear(); target.tryCatchBlocks.clear();
        if (target.localVariables != null) target.localVariables.clear();
        target.visibleLocalVariableAnnotations = null; target.invisibleLocalVariableAnnotations = null;
        target.instructions.add(new VarInsnNode(Opcodes.ALOAD, 0));
        target.instructions.add(new MethodInsnNode(Opcodes.INVOKESTATIC,
            london ? "forge/game/mulligan/LondonMulliganLimit" : "forge/game/mulligan/MulliganRoundProtocol",
            london ? "canMulligan" : "run",
            london ? "(Lforge/game/mulligan/LondonMulligan;)Z" : "(Lforge/game/mulligan/MulliganService;)V", false));
        target.instructions.add(new InsnNode(london ? Opcodes.IRETURN : Opcodes.RETURN));
        target.maxStack = 1; target.maxLocals = 1;
        ClassWriter writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
        node.accept(writer);
        byte[] result = writer.toByteArray();
        ClassNode check = new ClassNode(Opcodes.ASM8); new ClassReader(result).accept(check, 0);
        for (MethodNode m : check.methods) if (!(m.name.equals(targetName) && m.desc.equals(targetDesc)))
            if (!Arrays.equals(untouched.get(m.name + m.desc), methodBytes(m)))
                throw new IllegalStateException("Unrelated method changed: " + m.name);
        Files.write(Path.of(args[1]), result, StandardOpenOption.CREATE_NEW);
        System.out.println("PASS one "+targetName+" method replaced; " + untouched.size() + " other methods preserved");
    }
}
