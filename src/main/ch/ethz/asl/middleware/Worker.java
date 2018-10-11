package ch.ethz.asl.middleware;

import java.nio.channels.*;
import java.util.*;
import java.net.*;
import java.io.*;
import ch.ethz.asl.middleware.utils.*;

public class Worker implements Runnable {
    private ConnectionManager servers;
    private List<String> serverAddresses;
    private boolean readSharded;
    private final int id;
    private List<MiddlewareRequest> processedRequests;

    public Worker(List<String> serverAddresses, boolean readSharded, int id) {
        servers = new ConnectionManager(true);
        this.serverAddresses = serverAddresses;
        this.readSharded = readSharded;
        this.id = id;
        this.processedRequests = new ArrayList<>();
    }

    @Override
    public void run(){
        try {
            setupConnections(serverAddresses);
            System.out.println("Hello from Worker");
        } catch(Exception e){
            e.printStackTrace(System.out);
        }
    }

    private void setupConnections(List<String> serverAddresses) throws IOException {
        for (String address : serverAddresses){
            String[] parts = address.split(":");
            SocketChannel serverSocket = SocketChannel.open();
            InetSocketAddress serverAddress = new InetSocketAddress(parts[0], Integer.parseInt(parts[1]));
            serverSocket.connect(serverAddress);
            servers.addConnection(new Connection(serverSocket));
        }
    }

    private void printToStdout(String text){
        System.out.println("Time: " + System.nanoTime() + " Worker " + Integer.toString(this.id) + ": " + text);
    }

}


