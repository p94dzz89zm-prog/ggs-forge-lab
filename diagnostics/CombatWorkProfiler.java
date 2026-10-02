package forge.diagnostics;

import forge.game.combat.Combat;
import forge.game.card.Card;
import forge.game.player.Player;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

/** Diagnostic counters only. Matching observed inputs does not establish safe memoization. */
public final class CombatWorkProfiler {
    private static final class Search {
        long generation;
        final IdentityHashMap<Object,Integer> ids=new IdentityHashMap<>();
        final IdentityHashMap<Combat,Long> combatRevision=new IdentityHashMap<>();
        final Set<String> rawSeen=new HashSet<>(), observedSeen=new HashSet<>();
        int id(Object value) { return value==null ? 0 : ids.computeIfAbsent(value,k->ids.size()+1); }
    }
    private static final class Stats {
        final LongAdder calls=new LongAdder(), raw=new LongAdder(), observed=new LongAdder(), unstable=new LongAdder(), ns=new LongAdder(), repeatNs=new LongAdder();
    }
    private static final ThreadLocal<Search> current=new ThreadLocal<>();
    private static final Map<String,Stats> stats=new ConcurrentHashMap<>();
    static { Runtime.getRuntime().addShutdownHook(new Thread(CombatWorkProfiler::dump)); }

    public static final class Scope implements AutoCloseable {
        final Search previous;
        Scope() { previous=current.get(); if(previous==null)current.set(new Search()); }
        public void close() { if(previous==null)current.remove();else current.set(previous); }
    }
    public static Scope search() { return new Scope(); }
    public static void invalidate() { Search s=current.get();if(s!=null)s.generation++; }
    public static void combatChanged(Combat combat) { Search s=current.get();if(s!=null)s.combatRevision.merge(combat,1L,Long::sum); }
    private static String cardState(Card c) {
        if(c==null)return "null";
        return c.getCurrentStateName()+":"+c.getNetPower()+":"+c.getNetToughness()+":"+c.getDamage()+":"+c.isTapped()+":"+c.getCounters().hashCode()+":"+System.identityHashCode(c.getController());
    }
    public static final class Pair implements AutoCloseable {
        final Stats totals; final Search search; final Combat combat; final Card attacker,blocker; final Player ai;
        final long generation,revision,start; final String key,state; final boolean repeat;
        Pair(String method,Player ai,Card attacker,Card blocker,Combat combat,boolean without,boolean withoutStatic) {
            this.search=current.get();this.combat=combat;this.attacker=attacker;this.blocker=blocker;this.ai=ai;
            totals=stats.computeIfAbsent(method,k->new Stats());totals.calls.increment();
            generation=search==null ? -1 : search.generation;
            revision=search==null ? -1 : search.combatRevision.getOrDefault(combat,0L);
            state=cardState(attacker)+"/"+cardState(blocker)+"/"+(ai==null ? 0 : ai.getLife());
            String raw=search==null ? "" : method+":"+search.id(ai)+":"+search.id(attacker)+":"+search.id(blocker)+":"+search.id(combat)+":"+without+":"+withoutStatic;
            key=raw+":"+generation+":"+revision+":"+state;
            if(search!=null&&!search.rawSeen.add(raw))totals.raw.increment();
            repeat=search!=null&&search.observedSeen.contains(key);
            if(repeat)totals.observed.increment();
            start=System.nanoTime();
        }
        public void close() {
            long elapsed=System.nanoTime()-start;totals.ns.add(elapsed);if(repeat)totals.repeatNs.add(elapsed);
            if(search==null)return;
            if(search.generation==generation && search.combatRevision.getOrDefault(combat,0L)==revision
                && state.equals(cardState(attacker)+"/"+cardState(blocker)+"/"+(ai==null ? 0 : ai.getLife()))) {
                search.observedSeen.add(key);
            } else totals.unstable.increment();
        }
    }
    public static Pair pair(String method,Player ai,Card attacker,Card blocker,Combat combat,boolean without,boolean withoutStatic) {
        return new Pair(method,ai,attacker,blocker,combat,without,withoutStatic);
    }
    private static void dump() {
        String filename=System.getProperty("dragonmind.combatProfile");if(filename==null)return;
        var text=new StringBuilder("method,calls,raw_repeats,observed_state_repeats,changed_during_call,body_ns,observed_repeat_body_ns\n");
        for(String key:new TreeSet<>(stats.keySet())) {
            Stats s=stats.get(key);text.append(key).append(',').append(s.calls.sum()).append(',').append(s.raw.sum()).append(',').append(s.observed.sum()).append(',').append(s.unstable.sum()).append(',').append(s.ns.sum()).append(',').append(s.repeatNs.sum()).append('\n');
        }
        try {Files.writeString(Path.of(filename),text);}catch(Exception e){throw new RuntimeException(e);}
    }
}
