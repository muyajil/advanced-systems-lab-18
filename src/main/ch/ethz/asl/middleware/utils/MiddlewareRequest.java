package ch.ethz.asl.middleware.utils;

import java.util.List;

public class MiddlewareRequest {
    public int requestId;
    public String requestType;
    public List<String> commands;
    public int clientId;
    public int serverId;
    public int multiGetSize;
    public int receivedFromClient;
    public int enqueued;
    public int dequeued;
    public int queueLength;
    public int sentToServer;
    public int receivedFromServer;
    public int sentToclient;
    public boolean isSuccessful;
    public String response;
    public String error;
}
