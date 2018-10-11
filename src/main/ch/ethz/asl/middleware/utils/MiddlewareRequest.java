package ch.ethz.asl.middleware.utils;

import java.util.List;
import ch.ethz.asl.middleware.utils.Connection;

public class MiddlewareRequest {
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
}
