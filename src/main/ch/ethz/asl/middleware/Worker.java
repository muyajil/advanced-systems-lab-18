package ch.ethz.asl.middleware;

import java.nio.channels.*;
import java.util.*;
import java.net.*;
import java.io.*;
import ch.ethz.asl.middleware.utils.*;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class Worker implements Runnable {
    private ConnectionManager servers;
    private List<String> serverAddresses;
    private boolean readSharded;
    private final int id;
    private static final Logger logger = LogManager.getLogger("Worker");

    public Worker(List<String> serverAddresses, boolean readSharded, int id) {
        servers = new ConnectionManager(true);
        this.serverAddresses = serverAddresses;
        this.readSharded = readSharded;
        this.id = id;
    }

    @Override
    public void run(){
        try {
            setupConnections(serverAddresses);
            logger.trace("HelloWorld! from:" + this.id);
        } catch(Exception e){
            logger.error(e);
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
}


