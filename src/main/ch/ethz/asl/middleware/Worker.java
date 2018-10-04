package ch.ethz.asl.middleware;

import java.nio.channels.*;
import java.util.*;
import java.net.*;
//import ch.ethz.asl.middleware.utils.*;
import java.io.*;

public class Worker implements Runnable {
    private List<SocketChannel> memcachedSockets;
    private List<String> memcachedAddresses;
    private List<String> processedRequests = new ArrayList<>();
    private boolean readSharded;
    private final int id;
    private String[] responses;

    Worker(List<String> memcachedAddresses, boolean readSharded, int id) {
        this.memcachedAddresses = memcachedAddresses;
        this.memcachedSockets = new ArrayList<>();
        this.readSharded = readSharded;
        this.id = id;
        this.responses = new String[this.memcachedAddresses.size()];
        //setup();
    }

    @Override
    public void run(){
        
    }
}


