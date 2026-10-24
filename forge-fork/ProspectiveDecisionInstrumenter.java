import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;
public final class ProspectiveDecisionInstrumenter {
    public static void main(String[] args)throws Exception{
        ClassReader reader=new ClassReader(Files.readAllBytes(Path.of(args[0])));String owner=reader.getClassName();int[] hooks={0};
        ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){protected ClassLoader getClassLoader(){return ProspectiveDecisionInstrumenter.class.getClassLoader();}};
        reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);
                boolean priority=owner.equals("forge/game/Game")&&name.equals("fireEvent")&&Type.getArgumentTypes(desc).length==1;
                boolean decision=owner.equals("forge/ai/PlayerControllerAi")&&(access&(Opcodes.ACC_STATIC|Opcodes.ACC_ABSTRACT|Opcodes.ACC_SYNTHETIC))==0&&
                    (name.startsWith("choose")||name.startsWith("confirm")||name.startsWith("declare")||name.startsWith("assign")||name.startsWith("order")||name.equals("getAbilityToPlay")||name.equals("payManaCost")||name.equals("mulliganKeepHand"));
                decision|=owner.equals("forge/ai/validation/RulesValidationController")&&(name.equals("chooseSpellAbilityToPlay")||name.equals("playChosenSpellAbility"));
                if(!priority&&!decision)return mv;hooks[0]++;
                return new AdviceAdapter(Opcodes.ASM8,mv,access,name,desc){int token;
                    protected void onMethodEnter(){
                        if(priority){loadThis();loadArg(0);invokeStatic(Type.getObjectType("forge/ai/bridge/ProspectiveOpeningEvidence"),new Method("priorityEvent","(Lforge/game/Game;Ljava/lang/Object;)V"));return;}
                        push(name+desc);loadThis();loadArgArray();invokeStatic(Type.getObjectType("forge/ai/bridge/ProspectiveDecisionEvidence"),new Method("enter","(Ljava/lang/String;Lforge/game/player/PlayerController;[Ljava/lang/Object;)J"));token=newLocal(Type.LONG_TYPE);storeLocal(token);
                    }
                    protected void onMethodExit(int op){if(priority||op==ATHROW)return;Type ret=Type.getReturnType(desc);int value=-1;
                        if(op!=RETURN){value=newLocal(ret);storeLocal(value);}loadLocal(token);if(op==RETURN)visitInsn(ACONST_NULL);else{loadLocal(value);box(ret);}
                        invokeStatic(Type.getObjectType("forge/ai/bridge/ProspectiveDecisionEvidence"),new Method("leave","(JLjava/lang/Object;)V"));if(op!=RETURN)loadLocal(value);
                    }
                };
            }
        },ClassReader.EXPAND_FRAMES);
        if(hooks[0]<(owner.equals("forge/game/Game")?1:owner.equals("forge/ai/PlayerControllerAi")?20:2))throw new IllegalStateException("Missing prospective hooks");
        Files.write(Path.of(args[1]),writer.toByteArray(),StandardOpenOption.CREATE_NEW);System.out.println("PASS prospective decision hooks "+owner+":"+hooks[0]);
    }
}
