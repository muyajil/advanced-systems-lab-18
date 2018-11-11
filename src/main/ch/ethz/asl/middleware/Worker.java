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
    private int numServers;
    private final int id;
    private static final Logger logger = LogManager.getLogger("Worker");

    public Worker(List<String> serverAddresses, boolean readSharded, int id) {
        servers = new ConnectionManager(true);
        this.serverAddresses = serverAddresses;
        this.numServers = serverAddresses.size();
        this.readSharded = readSharded;
        this.id = id;
    }

    @Override
    public void run(){
        try {
            setupConnections(serverAddresses);
            while (!Thread.interrupted()) {
                MiddlewareRequest request = MiddlewareQueue.take();
                request.dequeueNano = request.getRealTimestamp(System.nanoTime());
                request.queueLength = MiddlewareQueue.getQueueLength();
                request.parse(numServers, readSharded);

                switch (request.requestType){
                    case "SET":
                        handleSetRequest(request);
                        break;
                    case "GET":
                        break;
                }

                // Finished processing request therefore we print it and give the connection back into the client pool
                logger.trace(request.toString());
                Clients.putConnection(request.connection);
            }
        } catch(Exception e){
            logger.error("Worker " + this.id + " " + e);
        }
    }

    private void handleSetRequest(MiddlewareRequest request) throws IOException{

        // send all requests
        for (int i = 0; i < numServers; i++){
            Connection server = servers.popConnection();
            server.write(request.commands.get(0));
            servers.putConnection(server);
        }

        request.sentToServerNano = request.getRealTimestamp(System.nanoTime());

        // gather responses
        String[] responses = new String[numServers];
        for (int i = 0; i < numServers; i ++){
            Connection server = servers.popConnection();
            responses[i] = server.read();
            servers.putConnection(server);
        }

        boolean allAreStored = true;

        for (String response : responses){
            allAreStored = allAreStored && response.equals("STORED\r\n");
        }

        if (allAreStored){
            request.isSuccessful = true;
            request.response = "STORED";
            request.connection.write("STORED\r\n");
        } else {
            request.isSuccessful = false;
            request.response = "NOT STORED";
            request.connection.write("NOT STORED\r\n");
        }

        request.returnedToClientNano = request.getRealTimestamp(System.nanoTime());
    }

    private void handleGetRequest(MiddlewareRequest request){

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


