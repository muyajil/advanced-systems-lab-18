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
                    } else{
                        requestType = "MUlTI-GET";
                        multiGetSize = elems.length - 1;
                    }
                } else{
                    if (elems.length <= 2){
                        requestType = "GET";
                    } else{
                        requestType = "MULTI-GET";
                        commands = shardCommand(elems, numServers);
                        multiGetSize = elems.length - 1;
                    }
                }
        }
    }

    private List<String> shardCommand(String[] keys, int numShards){
        // TODO
        throw new UnsupportedOperationException();
    }

    public String ToString(){
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