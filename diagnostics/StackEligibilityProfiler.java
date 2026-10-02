package forge.diagnostics;

import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.staticability.*;
import forge.game.ability.AbilityUtils;
import forge.game.zone.ZoneType;
import forge.util.FileSection;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/** Shadow-only. Every prediction is followed by the original complete rebuild. */
public final class StackEligibilityProfiler {
    public record Prediction(boolean skip, String reason) {}
    private record Plan(Map<String,String> params, Set<StaticAbilityLayer> layers,
                        boolean continuous, boolean cda, String kind) {}
    private static final ThreadLocal<IdentityHashMap<StaticAbility,Plan>> plans=new ThreadLocal<>();
    private static final Map<String,LongAdder[]> totals=new ConcurrentHashMap<>();
    private static final Map<String,Set<String>> examples=new ConcurrentHashMap<>();
    private static final LongAdder compiled=new LongAdder(), reused=new LongAdder(), lookups=new LongAdder(), lookupNs=new LongAdder();
    static { Runtime.getRuntime().addShutdownHook(new Thread(StackEligibilityProfiler::dump)); }
    public static final class Scope implements AutoCloseable {
        private final boolean root=plans.get()==null;
        Scope(){if(root)plans.set(new IdentityHashMap<>());}
        public void close(){if(root)plans.remove();}
    }
    public static Scope search(){return new Scope();}
    private static Plan compile(StaticAbility ability) {
        var params=Map.copyOf(ability.getMapParams());var layers=Set.copyOf(ability.getLayers());
        boolean continuous=ability.checkMode(StaticAbilityMode.Continuous), cda=ability.isCharacteristicDefining();
        var cache=plans.get();Plan old=cache==null?null:cache.get(ability);
        // Referenced SVars are read anew; their values can change without changing the parameter map.
        boolean generated=params.containsKey("AddStaticAbility")||params.containsKey("AddSVar")||params.containsKey("AddTrigger");
        if(!generated&&old!=null&&old.params.equals(params)&&old.layers.equals(layers)&&old.continuous==continuous&&old.cda==cda){reused.increment();return old;}
        String kind=classify(ability,params,layers,continuous,cda);
        Plan result=new Plan(params,layers,continuous,cda,kind);compiled.increment();
        if(!kind.equals("irrelevant")&&!kind.equals("assassin-grant")){
            Set<String> sample=examples.computeIfAbsent(kind,k->ConcurrentHashMap.newKeySet());
            if(sample.size()<20)sample.add(ability.getHostCard().getName()+" | "+new TreeMap<>(params));
        }
        if(cache!=null)cache.put(ability,result);return result;
    }
    private static String classify(StaticAbility ability,Map<String,String> params,Set<StaticAbilityLayer> layers,boolean continuous,boolean cda) {
        if(!continuous)return "irrelevant";
        if(layers.contains(StaticAbilityLayer.COPY))return "copy-layer";
        if(layers.contains(StaticAbilityLayer.CONTROL))return "control-layer";
        if(layers.contains(StaticAbilityLayer.TEXT))return "text-layer";
        if(pureLocalEffect(ability,params))return "local-defined";
        if(layers.contains(StaticAbilityLayer.TYPE))return cda&&layers.equals(Set.of(StaticAbilityLayer.TYPE))?"self-type-layer":"type-layer";
        for(String param:List.of("RemoveAllAbilities","RemoveNonManaAbilities","GainsAbilitiesOf","GainsAbilitiesOfDefined","GainsTriggerAbsOf","ShareRememberedKeywords"))
            if(params.containsKey(param))return "ability-rewrite";
        if(params.containsKey("AddStaticAbility")&&!benignGeneratedStatics(ability))return "generated-static";
        if(params.containsKey("AddSVar")&&!benignBlockingSVar(ability))return "generated-variable";
        boolean stack=ZoneType.listValueOf(params.getOrDefault("AffectedZone","Battlefield")).contains(ZoneType.Stack);
        if(layers.contains(StaticAbilityLayer.ABILITIES)&&(stack||cda||params.containsKey("AffectedDefined"))){
            if(isFreerunningGrant(params,layers,cda))return "assassin-grant";
            return "unknown-stack-grant";
        }
        // Unknown keywords may themselves generate continuous traits, even on another host.
        if(params.containsKey("AddKeyword")&&!benignKeywords(params.get("AddKeyword")))return "generated-keyword";
        if(params.containsKey("AddAbility")||params.containsKey("AddReplacementEffect"))return "generated-ability";
        if(params.containsKey("AddTrigger")&&!benignGeneratedTriggers(ability))return "generated-trigger";
        return "irrelevant";
    }
    private static boolean benignKeywords(String value){
        for(String keyword:value.split(" & "))
            if(!Set.of("Haste","Trample","Hexproof","Indestructible","Flying","First strike","Double strike","Menace","Vigilance","Lifelink","Deathtouch","Shroud","Reach","Skulk","Fear","Intimidate","Prevent all damage that would be dealt to CARDNAME.").contains(keyword)
                &&!keyword.startsWith("Protection:")&&!keyword.startsWith("Protection from "))return false;
        return true;
    }
    private static boolean pureLocalEffect(StaticAbility ability,Map<String,String> p){
        if(!Set.of("Self","Equipped","Enchanted").contains(p.getOrDefault("AffectedDefined","")))return false;
        if(!Set.of("Mode","Affected","AffectedDefined","AffectedZone","EffectZone","Description","Condition","CheckSVar","SVarCompare","AddPower","AddToughness","SetPower","SetToughness","AddType","RemoveType","RemoveCardTypes","RemoveSubTypes","RemoveSuperTypes","RemoveLandTypes","RemoveCreatureTypes","RemoveArtifactTypes","RemoveEnchantmentTypes","AddAllCreatureTypes","AddKeyword","AddTrigger","AddSVar").containsAll(p.keySet()))return false;
        if(p.containsKey("AddKeyword")&&!benignKeywords(p.get("AddKeyword")))return false;
        if(p.containsKey("AddTrigger")&&!benignGeneratedTriggers(ability))return false;
        return !p.containsKey("AddSVar")||benignBlockingSVar(ability);
    }
    private static Card definedTarget(StaticAbility ability){
        Card host=ability.getHostCard();
        if(ability.isCharacteristicDefining())return host;
        return switch(ability.getParam("AffectedDefined")){
            case "Self"->host;
            case "Equipped"->host.getEquipping();
            case "Enchanted"->host.getEnchantingCard();
            default->throw new IllegalStateException("Unknown local selector");
        };
    }
    private static boolean isFreerunningGrant(Map<String,String> p,Set<StaticAbilityLayer> layers,boolean cda){
        return !cda&&layers.equals(Set.of(StaticAbilityLayer.ABILITIES))
            &&Set.of("Mode","Affected","AffectedZone","AddKeyword","Description").containsAll(p.keySet())
            &&"Continuous".equals(p.get("Mode"))&&"Stack".equals(p.get("AffectedZone"))
            &&"Card.Assassin+YouCtrl+wasCast".equals(p.get("Affected"))
            &&"Freerunning:B B".equals(p.get("AddKeyword"));
    }
    private static boolean benignGeneratedStatics(StaticAbility ability){
        try{
            for(String name:ability.getParam("AddStaticAbility").split(" & ")){
                Map<String,String> p=FileSection.parseToMap(AbilityUtils.getSVar(ability,name),FileSection.DOLLAR_SIGN_KV_SEPARATOR);
                if(!"Continuous".equals(p.get("Mode"))||!"Battlefield".equals(p.getOrDefault("AffectedZone","Battlefield")))return false;
                if(!Set.of("Mode","Affected","AffectedZone","AddPower","AddToughness","SetPower","SetToughness","AddKeyword","Description","Condition","CheckSVar","SVarCompare").containsAll(p.keySet()))return false;
                if(p.containsKey("AddKeyword"))for(String keyword:p.get("AddKeyword").split(" & "))if(!Set.of("Haste","Trample").contains(keyword))return false;
            }
            return true;
        }catch(RuntimeException unknown){return false;}
    }
    private static boolean benignGeneratedTriggers(StaticAbility ability){
        try{
            for(String name:ability.getParam("AddTrigger").split(" & ")){
                Map<String,String> p=FileSection.parseToMap(AbilityUtils.getSVar(ability,name),FileSection.DOLLAR_SIGN_KV_SEPARATOR);
                String mode=p.get("Mode");
                if(mode==null||mode.equals("Always")||mode.equals("Immediate"))return false;
            }
            return true;
        }catch(RuntimeException unknown){return false;}
    }
    private static boolean benignBlockingSVar(StaticAbility ability){
        for(String name:ability.getParam("AddSVar").split(" & "))if(!"SVar:MustBeBlocked:AttackingPlayerConservative".equals(AbilityUtils.getSVar(ability,name)))return false;
        return true;
    }
    private static boolean potentialSource(StaticAbility ability,Card candidate){
        if(ability.isCharacteristicDefining())return true;
        Card host=ability.getHostCard();
        Set<ZoneType> active=ability.getActiveZone();
        if(active==null)active=Set.of(ZoneType.Battlefield);
        var zone=host.getGame().getZoneOf(host);
        if(zone!=null&&active.contains(zone.getZoneType()))return true;
        // The candidate is the only card whose zone changes in this hypothetical rebuild.
        // Ignore suppression and conditions, which may change while static effects are reset.
        return host.equals(candidate)&&active.contains(ZoneType.Stack);
    }
    public static Prediction predict(Card candidate,Player activator){
        long start=System.nanoTime();lookups.increment();
        try{return inspect(candidate,activator);}finally{lookupNs.add(System.nanoTime()-start);}
    }
    private static Prediction inspect(Card candidate,Player activator){
        if(candidate.isLKI())return new Prediction(false,"lki-candidate");
        if(candidate.getController()!=activator)return new Prediction(false,"borrowed-candidate");
        // Existing nonintrinsic keyword spells need not have come from a presently visible stack grant.
        for(var keyword:candidate.getUnhiddenKeywords())if(!keyword.isIntrinsic())return new Prediction(false,"extrinsic-candidate-keyword");
        List<StaticAbility> grants=new ArrayList<>();Set<String> hazards=new TreeSet<>();
        candidate.getGame().forEachCardInGame(card->{
            if(!card.getStaticCommandList().isEmpty())hazards.add("static-command");
            if(card.hasRemoveIntrinsic()||!card.getChangedCardTraitsByText().isEmpty()||!card.getChangedCardKeywordsByText().isEmpty())hazards.add("masked-source-traits");
            for(var changes:card.getChangedCardTraits().values())
                if(!(changes instanceof forge.game.card.CardTraitChanges known)||known.remove()!=null)hazards.add("masked-source-traits");
            for(var changes:card.getChangedCardKeywords().values())
                if(changes.isRemoveAllKeywords()||!changes.getRemoveKeywords().isEmpty()||!changes.getRemovedKeywordInstances().isEmpty())hazards.add("masked-source-keywords");
            List<StaticAbility> abilities=new ArrayList<>(card.getStaticAbilities());abilities.addAll(card.getHiddenStaticAbilities());
            for(StaticAbility ability:abilities){
                if(!potentialSource(ability,candidate))continue;
                Plan plan;
                try{plan=compile(ability);}catch(RuntimeException unknown){hazards.add("unknown-script");continue;}
                if(plan.kind.equals("assassin-grant"))grants.add(ability);
                else if(plan.kind.equals("local-defined")){
                    Card target=definedTarget(ability);
                    if(target!=null&&target.equals(candidate))hazards.add("candidate-local-effect");
                }
                else if(plan.kind.equals("self-type-layer")){if(ability.getHostCard().equals(candidate))hazards.add("candidate-self-type");}
                else if(!plan.kind.equals("irrelevant"))hazards.add(plan.kind);
            }
            return true;
        },true);
        if(!hazards.isEmpty())return new Prediction(false,String.join("+",hazards));
        if(grants.isEmpty())return new Prediction(false,"no-recognized-grant");
        for(StaticAbility grant:grants){
            // Do not trust present zone, suppression or activation conditions to remain unchanged.
            if(grant.getHostCard().getController()==candidate.getController()&&candidate.getType().hasCreatureType("Assassin"))return new Prediction(false,"possible-assassin-grant");
        }
        return new Prediction(true,"excluded-by-controller-or-subtype");
    }
    public static final class Query implements AutoCloseable {
        private final Prediction prediction;private final long start=System.nanoTime();private int added;private boolean completed;
        Query(Card candidate,Player player){prediction=predict(candidate,player);}
        public void completed(int additions){added=additions;completed=true;}
        public void close(){long ns=System.nanoTime()-start;LongAdder[] row=totals.computeIfAbsent(prediction.reason,k->new LongAdder[]{new LongAdder(),new LongAdder(),new LongAdder(),new LongAdder(),new LongAdder(),new LongAdder()});
            row[0].increment();if(prediction.skip)row[1].increment();if(completed&&added==0)row[2].increment();if(prediction.skip&&completed&&added>0)row[3].increment();row[4].add(ns);if(!completed)row[5].increment();}
    }
    public static Query query(Card candidate,Player player){return new Query(candidate,player);}
    private static void dump(){String file=System.getProperty("dragonmind.stackEligibilityProfile");if(file==null)return;
        StringBuilder output=new StringBuilder("reason,queries,predicted_skips,actual_empty,missed_productive_rebuilds,shadow_body_ns,incomplete\n");
        for(String reason:new TreeSet<>(totals.keySet())){output.append(reason);for(LongAdder value:totals.get(reason))output.append(',').append(value.sum());output.append('\n');}
        try{Files.writeString(Path.of(file),output);Files.writeString(Path.of(file+".index.csv"),"lookups,compiled_plans,reused_plans,lookup_ns\n"+lookups.sum()+","+compiled.sum()+","+reused.sum()+","+lookupNs.sum()+"\n");
            StringBuilder samples=new StringBuilder("reason\tscript_example\n");
            for(String reason:new TreeSet<>(examples.keySet()))for(String sample:new TreeSet<>(examples.get(reason)))samples.append(reason).append('\t').append(sample.replace("\n"," ").replace("\t"," ")).append('\n');
            Files.writeString(Path.of(file+".hazards.tsv"),samples);
        }catch(Exception e){throw new RuntimeException(e);}
    }
}
