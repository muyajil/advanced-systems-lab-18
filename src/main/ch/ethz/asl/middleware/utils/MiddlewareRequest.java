package ch.ethz.asl.middleware.utils;

import ch.ethz.asl.middleware.utils.Connection;
import java.util.*;

import static java.lang.Math.min;

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
    public int numKeysReturned;
    public long enqueueMilli;
    public long enqueueNano;
    public long dequeueNano;
    public int queueLength;
    public long sentToServerNano;
    public long receivedFromServerNano;
    public long returnedToClientNano;

    public void parse(int numServers, boolean readSharded){
        String command = commands.get(0);


        String[] elems = command.replace("\r\n", "").split(" ");
        
        switch(elems[0]){
            case "set":
                requestType = "SET";
                break;
            case "get":
                if (!readSharded){
                    if (elems.length < 3){
                        requestType = "GET";
                        multiGetSize = 1;
                    } else{
                        requestType = "MULTI-GET";
                        multiGetSize = elems.length - 1;
                    }
                } else{
                    if (elems.length < 3){
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

    private List<String> shardCommand(String[] commandElements, int numShards){
        List<String> commands = new ArrayList<>();
        int numKeys = commandElements.length-1;
        int minKeysPerShard = numKeys/numShards;
        int overflow = numKeys % numShards;
        int idx = 1;
        for (int i = 0; i < min(numShards, numKeys); i++){
            StringBuilder command = new StringBuilder();
            command.append("get ");
            for (int j = 0; j < minKeysPerShard; j++){
                command.append(commandElements[idx++]);
                command.append(" ");
            }

            if (overflow > 0){
                command.append(commandElements[idx++]);
                command.append(" ");
                overflow--;
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
            numKeysReturned +
            "," +
            isSuccessful +
            "," +
            enqueueNano +
            "," +
            dequeueNano +
            "," +
            sentToServerNano +
            "," +
            receivedFromServerNano +
            "," +
            returnedToClientNano +
            "," +
            queueLength;

    }

    public long getRealTimestamp(long nano){
        return (nano - enqueueNano) + enqueueMilli*1000;
    }

    public static String getHeader(){
        return "WorkerId,RequestId,RequestType,ClientId,ServerId,MultiGetSize,NumKeysReturned,IsSuccessful,EnqueueNano,DequeueNano,SentToServerNano,ReceivedFromServerNano,ReturnedToClientNano,QueueLength";
    }
}