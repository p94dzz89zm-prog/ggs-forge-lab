package forge.diagnostics;

import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.LongAdder;

/** Observe reconstruction; never reuse results or change engine decisions. */
public final class ReconstructionProfiler {
    private static final ThreadLocal<Set<Key>> seen=new ThreadLocal<>();
    private record Key(Card card, SpellAbility ability, Player player, boolean altOnly, Object face) {
        public boolean equals(Object other){return other instanceof Key k && card==k.card && ability==k.ability && player==k.player && altOnly==k.altOnly && face==k.face;}
        public int hashCode(){return Objects.hash(System.identityHashCode(card),System.identityHashCode(ability),System.identityHashCode(player),altOnly,System.identityHashCode(face));}
    }
    private static final LongAdder calls=new LongAdder(), repeats=new LongAdder(), stackCalls=new LongAdder(), empty=new LongAdder(), added=new LongAdder(), stackNs=new LongAdder(), restoreCalls=new LongAdder(), restoreNs=new LongAdder();
    static { Runtime.getRuntime().addShutdownHook(new Thread(ReconstructionProfiler::dump)); }
    public static final class Scope implements AutoCloseable {
        private final Set<Key> previous=seen.get();
        Scope(){ if(previous==null)seen.set(new HashSet<>()); }
        public void close(){ if(previous==null)seen.remove(); }
    }
    public static Scope search(){return new Scope();}
    public static void query(SpellAbility ability,Player player,boolean altOnly){
        calls.increment();Set<Key> set=seen.get();Card card=ability.getHostCard();
        if(set!=null&&!set.add(new Key(card,ability,player,altOnly,card.getCurrentStateName())))repeats.increment();
    }
    public static final class Timer implements AutoCloseable {
        private final boolean restoration; private final long start=System.nanoTime(); private int additions;
        Timer(boolean restoration){this.restoration=restoration;}
        public void added(int count){additions=count;}
        public void close(){long ns=System.nanoTime()-start;if(restoration){restoreCalls.increment();restoreNs.add(ns);}else{stackCalls.increment();stackNs.add(ns);added.add(additions);if(additions==0)empty.increment();}}
    }
    public static Timer stack(){return new Timer(false);}
    public static Timer restore(){return new Timer(true);}
    private static void dump(){String file=System.getProperty("dragonmind.reconstructionProfile");if(file==null)return;
        String output="queries,identity_repeats_in_discovery_scope,stack_rebuilds,stack_rebuilds_without_added_options,stack_added_options,stack_body_ns,restorations,restore_body_ns\n"+calls.sum()+","+repeats.sum()+","+stackCalls.sum()+","+empty.sum()+","+added.sum()+","+stackNs.sum()+","+restoreCalls.sum()+","+restoreNs.sum()+"\n";
        try{Files.writeString(Path.of(file),output);}catch(Exception e){throw new RuntimeException(e);}
    }
}
