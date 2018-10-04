package ch.ethz.asl.middleware;

import java.util.*;

public class Middleware implements Runnable{

    private final String ipAddress;
    private final int listenPort;
    private final boolean readSharded;
    private final List<Thread> workerThreads;
    private int requestId = 0;

    public Middleware(
        String ipAddress,
        int port,
        List<String> mcAddresses,
        int numThreads,
        boolean readSharded
    ){
        this.ipAddress = ipAddress;
        this.listenPort = port;
        this.readSharded = readSharded;
        this.workerThreads = new ArrayList<>();
    }

    public void run(){
        System.out.println("Hello from Middleware!");
    }
}