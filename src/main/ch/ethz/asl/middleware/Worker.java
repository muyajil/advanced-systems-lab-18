package ch.ethz.asl.middleware;

import ch.ethz.asl.middleware.utils.MiddlewareRequest;

import java.nio.channels.*;
import java.util.*;
import java.net.*;
//import ch.ethz.asl.middleware.utils.*;
import java.io.*;

public class Worker implements Runnable {
    private List<SocketChannel> memcachedConnections;
    private boolean readSharded;
    private final int id;

    Worker(List<String> memcachedAddresses, boolean readSharded, int id) {
        this.memcachedConnections = setupConnections(memcachedAddresses);
        this.readSharded = readSharded;
        this.id = id;
    }

    @Override
    public void run(){
        System.out.println("Hello from Worker");
    }

    private List<SocketChannel> setupConnections(List<String> memcachedAddresses){
        List<SocketChannel> memcachedConnections = new ArrayList<SocketChannel>();
        for (String address : memcachedAddresses){
            String[] parts = address.split(":");
            try{
                SocketChannel memcachedSocket = SocketChannel.open();
                InetSocketAddress memcachedAddress = new InetSocketAddress(
                        parts[0],
                        Integer.parseInt(parts[1]));
                memcachedSocket.connect(memcachedAddress);
                memcachedConnections.add(memcachedSocket);
            } catch (IOException e){
                printToStdout("Reporting and exception:");
                e.printStackTrace(System.out);
            }
        }

        return memcachedConnections;
    }

    private void printToStdout(String text){
        System.out.println("Time: " + System.nanoTime() + " Worker " + Integer.toString(this.id) + ": " + text);
    }

}


