import forge.view.SimulateMatch;
public class MemoryRetentionCheck {
 public static void main(String[] args)throws Exception {
  forge.gui.GuiBase.setInterface(new forge.GuiDesktop());
  SimulateMatch.simulate(args);
  for(int i=0;i<3;i++){System.gc();Thread.sleep(100);}
  long retained=SimulateMatch.auditGames.stream().filter(r->r.get()!=null).count();
  long evalThreads=Thread.getAllStackTraces().keySet().stream().filter(t->t.isAlive()&&t.getName().equals("Game AI Eval")).count();
  System.out.println("Memory Audit: games="+SimulateMatch.auditGames.size()+", retained_games="+retained+", live_eval_threads="+evalThreads+", used_heap_bytes="+(Runtime.getRuntime().totalMemory()-Runtime.getRuntime().freeMemory()));
  if(retained!=0||evalThreads!=0)throw new AssertionError("game or evaluator retained after batch");
 }
}
