package ch.ethz.asl.middleware.utils;

import ch.ethz.asl.middleware.utils.Connection;
import java.util.*;

public class MiddlewareRequest {
    public int workerId;
    public int requestId;
    public Connection connection;
    public String requestType;
    public List<String> commands;
    public int clientId;
    public int serverId;
    public int multiGetSize;
    public boolean isSuccessful;
    public String response;
    public String error;
    public long enqueueMilli;
    public long enqueueNano;
    public long dequeueNano;
    public int queueLength;
    public long sentToServerNano;
    public long returnedToClientNano;

    public void parse(int numServers, boolean readSharded){
        String command = commands.get(0);

        String[] elems = command.split(" ");
        
        switch(elems[0]){
            case "set":
                requestType = "SET";
                break;
            case "get":
                if (!readSharded){
                    if (elems.length <= 2){
                        requestType = "GET";
                        multiGetSize = 1;
                    } else{
                        requestType = "MUlTI-GET";
                        multiGetSize = elems.length - 1;
                    }
                } else{
                    if (elems.length <= 2){
                        requestType = "GET";
                        multiGetSize = 1;
                    } else{
                        requestType = "MULTI-GET";
                        commands = shardCommand(elems, numServers);
                        multiGetSize = elems.length - 1;
                    }
                }
                break;
            default:
                break;
        }
    }

    private List<String> shardCommand(String[] keys, int numShards){
        List<String> commands = new ArrayList<>();
        int minKeysPerShard = keys.length/numShards;
        int overflow = keys.length % numShards;
        int idx = 0;
        for (int i = 0; i < numShards; i++){
            StringBuilder command = new StringBuilder();
            command.append("get ");
            for (int j = 0; j < minKeysPerShard; j++){
                command.append(keys[idx++]);
                command.append(" ");

                if (overflow > 0){
                    command.append(keys[idx++]);
                    command.append(" ");
                    overflow--;
                }
            }
            command.append("\r\n");
            commands.add(command.toString());
        }
        return commands;
    }

    public String toString(){
        return workerId + 
            "," +
            requestId + 
            "," +
            requestType +
            "," +
            clientId +
            "," +
            serverId +
            "," +
            multiGetSize +
            "," +
            isSuccessful +
            "," +
            response +
            "," +
            error +
            "," +
            enqueueNano +
            "," +
            dequeueNano +
            "," +
            sentToServerNano +
            "," +
            returnedToClientNano +
            "," +
            queueLength;

    }

    public long getRealTimestamp(long nano){
        return (nano - enqueueNano) + enqueueMilli*1000;
    }

    public static String getHeader(){
        return "WorkerId,RequestId,RequestType,ClientId,ServerId,MultiGetSize,IsSuccessful,Response,Error,EnqueueNano,DequeueNano,SentToServerNano,ReturnedToClientNano,QueueLength";
    }
}