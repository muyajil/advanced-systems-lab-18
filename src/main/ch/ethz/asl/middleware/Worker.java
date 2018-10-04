package ch.ethz.asl.middleware;

import ch.ethz.asl.middleware.utils.MiddlewareRequest;

import java.nio.channels.*;
import java.util.*;
import java.net.*;
//import ch.ethz.asl.middleware.utils.*;
import java.io.*;

public class Worker implements Runnable {
    private List<String> memcachedAddresses;
    private boolean readSharded;
    private final int id;

    Worker(List<String> memcachedAddresses, boolean readSharded, int id) {
        this.memcachedAddresses = memcachedAddresses;
        this.readSharded = readSharded;
        this.id = id;
    }

    @Override
    public void run(){
        System.out.println("Hello from Worker");
    }
}


