import jdk.jfr.consumer.*;
import java.nio.file.*;
import java.util.*;

/** Sampling evidence; inclusive hit counts are not elapsed stage timings. */
public class JfrDecisionPaths {
    public static void main(String[] args) throws Exception {
        Map<String,Long> leaves=new HashMap<>(), paths=new HashMap<>(), inclusive=new HashMap<>(), allocations=new HashMap<>();
        long total=0, engine=0;
        Set<String> targets=Set.of("getAllPossibleAbilities","getSpellAbilities","getAlternativeCosts","alternativeCosts",
            "getAlternateHost","checkStaticAbilities","getReplacementList","predictNextCombatsRemainingLife",
            "assignBlockersForCombat","declareAttackers","evaluateBoardPositionChanged","canPlayAndPayFor","canPlaySa");
        try(var recording=new RecordingFile(Path.of(args[0]))) {
            while(recording.hasMoreEvents()) {
                var event=recording.readEvent(); var stack=event.getStackTrace();
                if(stack==null) continue;
                List<String> forge=new ArrayList<>(); Set<String> matched=new HashSet<>();
                for(var frame:stack.getFrames()) {
                    String cls=frame.getMethod().getType().getName(), name=frame.getMethod().getName();
                    if(cls.startsWith("forge.")) {
                        forge.add(cls+"."+name);
                        if(targets.contains(name)) matched.add(cls+"."+name);
                    }
                }
                if(event.getEventType().getName().equals("jdk.ExecutionSample")) {
                    total++;
                    if(forge.isEmpty())continue;
                    engine++;
                    leaves.merge(forge.get(0),1L,Long::sum);
                    paths.merge(String.join(" <- ",forge.subList(0,Math.min(8,forge.size()))),1L,Long::sum);
                    for(String name:matched)inclusive.merge(name,1L,Long::sum);
                } else if(event.getEventType().getName().equals("jdk.ObjectAllocationSample") && !forge.isEmpty()) {
                    allocations.merge(forge.get(0),event.getLong("weight"),Long::sum);
                }
            }
        }
        System.out.println("Execution samples="+total+"; with Forge frame="+engine);
        print("Top Forge leaf frames (sample hits)",leaves,15);
        print("Decision paths (sample hits)",paths,15);
        print("Inclusive target hits (overlap; do not add)",inclusive,30);
        print("Sampled allocation weight by nearest Forge frame (bytes; estimates)",allocations,15);
    }
    static void print(String heading,Map<String,Long> values,int limit) {
        System.out.println(heading);
        values.entrySet().stream().sorted(Map.Entry.<String,Long>comparingByValue().reversed()).limit(limit)
            .forEach(entry->System.out.println(entry.getValue()+"\t"+entry.getKey()));
    }
}
