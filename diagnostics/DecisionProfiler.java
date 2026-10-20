package forge.diagnostics;

import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

/** Diagnostic nested wall timings; exclusive time excludes instrumented children only. */
public final class DecisionProfiler {
    private static final class Stats {
        final LongAdder calls=new LongAdder(), inclusive=new LongAdder(), exclusive=new LongAdder();
    }
    private static final Map<String,Stats> totals=new ConcurrentHashMap<>();
    private static final ThreadLocal<Scope> active=new ThreadLocal<>();
    static { Runtime.getRuntime().addShutdownHook(new Thread(DecisionProfiler::dump)); }
    public static final class Scope implements AutoCloseable {
        final Scope parent; final Stats stats; final long started; final String path;
        final boolean validitySample;
        long children;
        Scope(String label) {
            parent=active.get();
            validitySample=label.equals("validity-sample") || (parent!=null && parent.validitySample);
            path=parent==null ? Thread.currentThread().getName()+" :: "+label : parent.path+" > "+label;
            stats=totals.computeIfAbsent(path,k->new Stats());
            active.set(this); started=System.nanoTime();
        }
        public void close() {
            long elapsed=System.nanoTime()-started;
            stats.calls.increment(); stats.inclusive.add(elapsed); stats.exclusive.add(elapsed-children);
            if(parent!=null)parent.children+=elapsed;
            active.set(parent);
        }
    }
    public static Scope enter(String label) { return new Scope(label); }
    private static final ThreadLocal<long[]> validitySequence=ThreadLocal.withInitial(() -> new long[1]);
    /** Independent deterministic sample; never touches the engine RNG. */
    public static Scope beginValiditySample() {
        Scope current=active.get();
        if (current==null || !current.path.endsWith("affected-validity") || current.validitySample) return null;
        long value=++validitySequence.get()[0];
        value=(value^(value>>>30))*0xbf58476d1ce4e5b9L;
        value=(value^(value>>>27))*0x94d049bb133111ebL;
        value=value^(value>>>31);
        return (value & 63L)==0 ? enter("validity-sample") : null;
    }
    public static boolean inValiditySample() { Scope s=active.get(); return s!=null && s.validitySample; }
    private static void dump() {
        String filename=System.getProperty("dragonmind.decisionProfile"); if(filename==null)return;
        StringBuilder out=new StringBuilder("path,calls,inclusive_ns,exclusive_ns\n");
        for(String key:new TreeSet<>(totals.keySet())) {
            Stats s=totals.get(key);
            out.append(key).append(',').append(s.calls.sum()).append(',').append(s.inclusive.sum()).append(',').append(s.exclusive.sum()).append('\n');
        }
        try { Files.writeString(Path.of(filename),out); } catch(Exception e) { throw new RuntimeException(e); }
    }
}
