import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;

/** Opt-in controller factory only; no rules or Stage48 replay classes changed. */
public class ValidationPilotInstrumenter {
    public static void main(String[] args) throws Exception {
        ClassReader r=new ClassReader(Files.readAllBytes(Path.of(args[0])));
        ClassWriter w=new ClassWriter(r,ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){
            protected String getCommonSuperClass(String a,String b){
                try{
                    ClassLoader loader=ValidationPilotInstrumenter.class.getClassLoader();
                    Class<?> x=Class.forName(a.replace('/','.'),false,loader),y=Class.forName(b.replace('/','.'),false,loader);
                    if(x.isAssignableFrom(y))return a;if(y.isAssignableFrom(x))return b;
                    if(x.isInterface()||y.isInterface())return "java/lang/Object";
                    do{x=x.getSuperclass();}while(!x.isAssignableFrom(y));
                    return x.getName().replace('.','/');
                }catch(ClassNotFoundException e){throw new IllegalStateException(e);}
            }
        };
        int[] count={0};
        r.accept(new ClassVisitor(Opcodes.ASM8,w){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);
                if(!name.equals("createControllerFor") || !desc.equals("(Lforge/game/player/Player;)Lforge/ai/PlayerControllerAi;"))return mv;
                return new MethodVisitor(Opcodes.ASM8,mv){
                    public void visitVarInsn(int op,int index){
                        super.visitVarInsn(op,index);
                        if(op==Opcodes.ASTORE && index==2){
                            super.visitVarInsn(Opcodes.ALOAD,2);super.visitVarInsn(Opcodes.ALOAD,1);super.visitVarInsn(Opcodes.ALOAD,0);
                            super.visitMethodInsn(Opcodes.INVOKESTATIC,"forge/ai/validation/RulesValidationController","wrap",
                                "(Lforge/ai/PlayerControllerAi;Lforge/game/player/Player;Lforge/LobbyPlayer;)Lforge/ai/PlayerControllerAi;",false);
                            super.visitVarInsn(Opcodes.ASTORE,2);count[0]++;
                        }
                    }
                };
            }
        },ClassReader.EXPAND_FRAMES);
        if(count[0]!=1)throw new IllegalStateException("Unexpected controller factory: "+count[0]);
        Files.write(Path.of(args[1]),w.toByteArray(),StandardOpenOption.CREATE_NEW);
        System.out.println("PASS one opt-in validation factory hook");
    }
}
