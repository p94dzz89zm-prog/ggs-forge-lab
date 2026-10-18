package forge.ai.bridge;

import com.google.gson.*;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Fail-closed offline evidence. A partial file is never a completed stream. */
public final class DurableEvidence {
    private DurableEvidence() {}
    private static String gameId;
    private static boolean sealed;
    private static final Map<Path,Stream> streams=new LinkedHashMap<>();
    private static final class Stream {
        final Path target,partial; final FileChannel channel; final MessageDigest hash;
        long rows,bytes;
        Stream(Path p)throws Exception {
            target=p.toAbsolutePath();partial=target.resolveSibling(target.getFileName()+".partial");
            Files.createDirectories(target.getParent());
            if(Files.exists(target)||Files.exists(target.resolveSibling(target.getFileName()+".receipt.json")))throw new IOException("Evidence already exists: "+target);
            channel=FileChannel.open(partial,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            hash=MessageDigest.getInstance("SHA-256");
        }
    }
    public static synchronized void begin(String id)throws IOException {
        if(!streams.isEmpty())throw new IOException("Unfinalized prior evidence streams");
        gameId=id;sealed=false;
    }
    public static synchronized void append(Path path,String line)throws IOException {
        // Keep non-game diagnostic callers compatible; game collection always calls begin.
        if(gameId==null){BridgeChannel.append(path,line);return;}
        if(sealed)throw new IOException("Write after evidence finalization");
        try {
            Path key=path.toAbsolutePath();Stream s=streams.get(key);
            if(s==null){s=new Stream(key);streams.put(key,s);}
            JsonObject row=JsonParser.parseString(line).getAsJsonObject();
            row.addProperty("evidence_game_id",gameId);row.addProperty("stream_sequence",s.rows+1);
            byte[] data=(row+"\n").getBytes(StandardCharsets.UTF_8);
            ByteBuffer b=ByteBuffer.wrap(data);while(b.hasRemaining())s.channel.write(b);
            s.hash.update(data);s.rows++;s.bytes+=data.length;
            if(s.rows%128==0){s.channel.force(true);JsonObject progress=new JsonObject();progress.addProperty("game_id",gameId);progress.addProperty("records_written",s.rows);progress.addProperty("bytes_written",s.bytes);progress.addProperty("write_status","in_progress");atomic(s.partial.resolveSibling(s.partial.getFileName()+".progress.json"),progress.toString());}
        } catch(Exception e){throw new IOException("Evidence append failed",e);}
    }
    public static String hash(byte[] data)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(data));}
    public static void syncDirectory(Path directory)throws IOException {
        try(FileChannel c=FileChannel.open(directory,StandardOpenOption.READ)){c.force(true);}
    }
    public static void atomic(Path target,String content)throws IOException {
        Files.createDirectories(target.toAbsolutePath().getParent());
        Path temp=target.resolveSibling(target.getFileName()+"."+UUID.randomUUID()+".partial");
        try(FileChannel c=FileChannel.open(temp,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            ByteBuffer b=StandardCharsets.UTF_8.encode(content);while(b.hasRemaining())c.write(b);c.force(true);
        }
        // No non-atomic fallback. An unsupported filesystem is an explicit failure.
        Files.move(temp,target,StandardCopyOption.ATOMIC_MOVE);syncDirectory(target.toAbsolutePath().getParent());
    }
    public static synchronized void finish(Path directory,long seed,String transcript,JsonObject result)throws IOException {
        try {
            sealed=true;JsonArray receipts=new JsonArray();boolean complete=result.get("status").getAsString().startsWith("completed");
            for(Stream s:streams.values()) {
                s.channel.force(true);s.channel.close();
                String want=HexFormat.of().formatHex(s.hash.digest());
                if(Files.size(s.partial)!=s.bytes||!hash(Files.readAllBytes(s.partial)).equals(want))throw new IOException("Stream changed before finalization");
                JsonObject receipt=new JsonObject();receipt.addProperty("format",1);receipt.addProperty("game_id",gameId);receipt.addProperty("records",s.rows);receipt.addProperty("bytes",s.bytes);receipt.addProperty("sha256",want);receipt.addProperty("write_status",complete?"complete":"interrupted");receipt.addProperty("file",directory.toAbsolutePath().getParent().getParent().relativize(s.target).toString());
                if(complete){Files.move(s.partial,s.target,StandardCopyOption.ATOMIC_MOVE);syncDirectory(s.target.getParent());atomic(s.target.resolveSibling(s.target.getFileName()+".receipt.json"),receipt.toString());}
                receipts.add(receipt);
            }
            Path text=directory.resolve(seed+".log"),record=directory.resolve(seed+".json");
            if(Files.exists(text)||Files.exists(record)||Files.exists(directory.resolve(seed+".evidence.json")))throw new IOException("Existing game evidence");
            atomic(text,transcript);atomic(record,result.toString());
            JsonObject manifest=new JsonObject();manifest.addProperty("format",1);manifest.addProperty("game_id",gameId);manifest.addProperty("seed",seed);manifest.addProperty("write_status",complete?"complete":"interrupted");manifest.addProperty("completion_marker",complete?"DRAGONMIND_EVIDENCE_COMPLETE":"DRAGONMIND_EVIDENCE_INTERRUPTED");manifest.addProperty("transcript_sha256",hash(transcript.getBytes(StandardCharsets.UTF_8)));manifest.addProperty("transcript_records",transcript.lines().count());manifest.addProperty("result_sha256",hash(result.toString().getBytes(StandardCharsets.UTF_8)));manifest.add("streams",receipts);
            atomic(directory.resolve(seed+".evidence.json"),manifest.toString());streams.clear();
        }catch(Exception e){throw new IOException("Evidence finalization failed; partial files retained",e);}
    }
}
