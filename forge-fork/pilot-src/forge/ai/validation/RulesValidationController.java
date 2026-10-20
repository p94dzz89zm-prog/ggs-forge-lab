package forge.ai.validation;

import com.google.gson.*;
import forge.LobbyPlayer;
import forge.ai.*;
import forge.ai.bridge.*;
import forge.game.*;
import forge.game.card.*;
import forge.game.player.Player;
import forge.game.spellability.*;
import forge.game.zone.ZoneType;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

/** Experimental deterministic interaction policy; all execution stays in Forge. */
public final class RulesValidationController extends PlayerControllerBridge {
    public static final String VERSION = "native-rules-validation-v1";
    private final Map<String,Integer> kinds = new HashMap<>(), visits = new HashMap<>();
    private String budgetPhase = "";
    private int phaseActions;
    private long revision;
    private SpellAbility selected;

    public RulesValidationController(Game g, Player p, LobbyPlayer l) { super(g,p,l); }

    public static PlayerControllerAi wrap(PlayerControllerAi original, Player p, LobbyPlayer l) {
        if (!Boolean.getBoolean("dragonmind.validationPilot")) return original;
        if (System.getProperty("forge.bridge.player") != null || DecisionReplay.enabled())
            throw new IllegalStateException("Validation pilot cannot share remote/replay ownership");
        Long.parseLong(System.getProperty("dragonmind.validationSeed")); // Required frozen input.
        return new RulesValidationController(p.getGame(),p,l);
    }

    private static String token(SpellAbility a) {return a.getHostCard().getId()+":"+a.getId();}
    private static String kind(SpellAbility a) {return a.isLandAbility()?"land":a.isSpell()?"spell":"activated";}
    private String tie(SpellAbility a) {
        try {
            String input=System.getProperty("dragonmind.validationSeed")+":"+player.getId()+":"+revision+":"+token(a);
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(input.getBytes(StandardCharsets.UTF_8)));
        } catch(Exception e) {throw new IllegalStateException(e);}
    }
    private void audit(List<SpellAbility> result,int candidates,int rejected,String reason) {
        String dir=System.getProperty("forge.audit.directory");if(dir==null)return;
        JsonObject row=new JsonObject();row.addProperty("kind","priority");
        row.add("state",forge.ai.ggs.PlannerSnapshot.forPlayer(player));
        JsonObject d=new JsonObject();d.addProperty("policy",VERSION);d.addProperty("revision",revision);
        d.addProperty("candidate_count",candidates);d.addProperty("engine_preflight_rejections",rejected);
        d.addProperty("reason",reason);d.addProperty("selected",result==null?null:token(result.get(0)));
        d.addProperty("target_assistance","Forge stock target chooser; combat and other hooks delegated");row.add("decision",d);
        try {DurableEvidence.append(Path.of(dir,"seat-"+player.getId()+".jsonl"),row.toString());}
        catch(java.io.IOException e) {throw new IllegalStateException(e);}
    }
    private boolean targetsValid(SpellAbility a) {
        for(SpellAbility p=a;p!=null;p=p.getSubAbility())
            if(p.usesTargeting()) {
                if(!p.isTargetNumberValid())return false;
                for(GameObject target:p.getTargets())if(!p.canTarget(target))return false;
            }
        return true;
    }
    @Override public List<SpellAbility> chooseSpellAbilityToPlay() {
        if(forge.ai.ggs.PlannerContext.active())return super.chooseSpellAbilityToPlay();
        long call=EngineEvidence.enter("forge/ai/validation/RulesValidationController.chooseSpellAbilityToPlay()Ljava/util/List;",this,new Object[0]);
        List<SpellAbility> result=null;
        try {
            selected=null;revision++;
            String phase=getGame().getPhaseHandler().getTurn()+":"+getGame().getPhaseHandler().getPhase();
            if(!phase.equals(budgetPhase)){budgetPhase=phase;phaseActions=0;}
            // Legal policy pass bounds repeatable zero-cost activations; never ends a game.
            if(phaseActions>=64){audit(null,0,0,"policy phase-action budget");return null;}
            CardCollection cards=new CardCollection(player.getCardsIn(ZoneType.Hand,ZoneType.Graveyard,ZoneType.Command));
            cards.addAll(player.getCardsIn(ZoneType.Battlefield));
            for(Card c:player.getCardsIn(ZoneType.Exile))if(!c.isFaceDown())cards.add(c);
            List<SpellAbility> candidates=new ArrayList<>();
            CardCollection lands=ComputerUtilAbility.getAvailableLandsToPlay(getGame(),player);
            if(lands!=null)for(Card c:lands)if(!c.isInZone(ZoneType.Library)){
                LandAbility a=new LandAbility(c,c.getCurrentState());a.setActivatingPlayer(player);
                if(a.canPlay())candidates.add(a);
            }
            for(SpellAbility a:ComputerUtilAbility.getSpellAbilities(cards,player)){
                a.setActivatingPlayer(player);
                if(!a.isManaAbility() && a.canPlay())candidates.add(a);
            }
            candidates.sort(Comparator.comparingInt((SpellAbility a)->kinds.getOrDefault(kind(a),0))
                .thenComparingInt(a->visits.getOrDefault(token(a),0)).thenComparing(this::tie));
            int rejected=0;
            for(SpellAbility a:candidates){
                if(!a.isLandAbility() && !ComputerUtilCost.canPayCost(a,player,false)){rejected++;continue;}
                boolean targets=true;
                for(SpellAbility part=a;part!=null;part=part.getSubAbility())
                    if(part.usesTargeting() && !super.chooseTargetsFor(part)){targets=false;break;}
                if(!targets || !targetsValid(a) || !a.canPlay()){rejected++;continue;}
                selected=a;phaseActions++;kinds.merge(kind(a),1,Integer::sum);visits.merge(token(a),1,Integer::sum);
                result=Collections.singletonList(a);audit(result,candidates.size(),rejected,"engine-preflighted selection");return result;
            }
            audit(null,candidates.size(),rejected,"no executable candidate in supported source zones");return null;
        } finally {EngineEvidence.leave(call,result);}
    }
    @Override public boolean playChosenSpellAbility(SpellAbility a) {
        long call=EngineEvidence.enter("forge/ai/validation/RulesValidationController.playChosenSpellAbility(Lforge/game/spellability/SpellAbility;)Z",this,new Object[]{a});
        boolean result;
        try {
            result=executeChosen(a);
        } catch(RuntimeException|Error e){
            EngineEvidence.leave(call,Map.of("execution_exception",e.getClass().getName()));throw e;
        }
        EngineEvidence.leave(call,result);return result;
    }
    private boolean executeChosen(SpellAbility a) {
        if(a==null || a!=selected || a.getActivatingPlayer()!=player || getGame().getPhaseHandler().getPriorityPlayer()!=player
                || !a.canPlay() || !targetsValid(a))return false;
        selected=null;
        if(a.isLandAbility()){a.resolve();return true;}
        return ComputerUtil.handlePlayingSpellAbility(player,a,null);
    }
}
