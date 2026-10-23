import java.nio.file.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.commons.*;

/** Append observers to exact native boundaries; preserve original execution. */
public final class ProspectiveOpeningInstrumenter {
    static final Type OBS=Type.getObjectType("forge/ai/bridge/ProspectiveOpeningEvidence");
    public static void main(String[] args)throws Exception{
        ClassReader reader=new ClassReader(Files.readAllBytes(Path.of(args[0])));String owner=reader.getClassName();int[] hooks={0},permutations={0};
        ClassWriter writer=new ClassWriter(reader,ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){
            protected ClassLoader getClassLoader(){return ProspectiveOpeningInstrumenter.class.getClassLoader();}
        };
        reader.accept(new ClassVisitor(Opcodes.ASM8,writer){
            public MethodVisitor visitMethod(int access,String name,String desc,String sig,String[] ex){
                MethodVisitor mv=super.visitMethod(access,name,desc,sig,ex);String hook=null;
                if(owner.equals("forge/game/player/Player")&&name.equals("shuffle")&&desc.equals("(Lforge/game/spellability/SpellAbility;)V"))hook="shuffle";
                if(owner.equals("forge/game/GameAction")&&name.equals("determineFirstTurnPlayer"))hook="starting_player_selection";
                if(owner.equals("forge/game/mulligan/MulliganService")&&name.equals("perform"))hook="mulligans";
                if(owner.equals("forge/ai/PlayerControllerAi")&&name.equals("chooseStartingPlayer"))hook="starting_player_choice";
                if(owner.equals("forge/ai/PlayerControllerAi")&&name.equals("mulliganKeepHand"))hook="mulligan_decision";
                if(owner.equals("forge/ai/PlayerControllerAi")&&name.equals("tuckCardsViaMulligan"))hook="bottom_choice";
                boolean random=owner.equals("forge/ai/bridge/EvidenceRandom")&&name.equals("next")&&desc.equals("(I)I");
                if(hook==null&&!random)return mv;hooks[0]++;final String tag=hook;
                return new AdviceAdapter(Opcodes.ASM8,mv,access,name,desc){
                    int token;
                    protected void onMethodEnter(){if(random)return;
                        push(tag);loadThis();loadArgArray();invokeStatic(OBS,new Method("enter","(Ljava/lang/String;Ljava/lang/Object;[Ljava/lang/Object;)J"));token=newLocal(Type.LONG_TYPE);storeLocal(token);
                    }
                    protected void onMethodExit(int op){if(op==ATHROW)return;Type ret=Type.getReturnType(desc);int result=-1;
                        if(op!=RETURN){result=newLocal(ret);storeLocal(result);}
                        if(random){loadArg(0);loadLocal(result);invokeStatic(OBS,new Method("random","(II)V"));}
                        else {loadLocal(token);if(op==RETURN)visitInsn(ACONST_NULL);else{loadLocal(result);box(ret);}invokeStatic(OBS,new Method("leave","(JLjava/lang/Object;)V"));}
                        if(op!=RETURN)loadLocal(result);
                    }
                    public void visitMethodInsn(int op,String target,String method,String descriptor,boolean itf){
                        boolean shuffle="shuffle".equals(tag)&&target.equals("java/util/Collections")&&method.equals("shuffle")&&descriptor.equals("(Ljava/util/List;Ljava/util/Random;)V");
                        int list=-1;
                        if(shuffle){dup2();int rng=newLocal(Type.getType(java.util.Random.class));storeLocal(rng);list=newLocal(Type.getType(java.util.List.class));storeLocal(list);}
                        super.visitMethodInsn(op,target,method,descriptor,itf);
                        if(shuffle){loadThis();loadLocal(list);invokeStatic(OBS,new Method("generated","(Lforge/game/player/Player;Ljava/lang/Iterable;)V"));permutations[0]++;}
                    }
                };
            }
        },ClassReader.EXPAND_FRAMES);
        int expected=owner.equals("forge/ai/PlayerControllerAi")?3:1;
        if(hooks[0]!=expected||owner.equals("forge/game/player/Player")&&permutations[0]!=1)throw new IllegalStateException("Unexpected opening hook inventory "+owner+":"+hooks[0]);
        Files.write(Path.of(args[1]),writer.toByteArray(),StandardOpenOption.CREATE_NEW);System.out.println("PASS opening observers "+owner+":"+hooks[0]);
    }
}
