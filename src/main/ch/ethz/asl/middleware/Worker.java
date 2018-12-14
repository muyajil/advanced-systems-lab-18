package ch.ethz.asl.middleware;

import java.nio.ByteBuffer;
import java.nio.channels.*;
import java.util.*;
import java.net.*;
import java.io.*;
import ch.ethz.asl.middleware.utils.*;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class Worker implements Runnable {
    private ServerManager servers;
    private List<String> serverAddresses;
    private boolean readSharded;
    private int numServers;
    private final int id;
    private static final Logger logger = LogManager.getLogger("Worker");
    private ByteBuffer readBuffer;

    public Worker(List<String> serverAddresses, boolean readSharded, int id) {
        this.serverAddresses = serverAddresses;
        this.numServers = serverAddresses.size();
        this.readSharded = readSharded;
        this.id = id;
        servers = new ServerManager(true, numServers);
        this.readBuffer = ByteBuffer.allocate(65536);
    }

    @Override
    public void run(){
        try {
            setupConnections(serverAddresses);
            while (!Thread.currentThread().isInterrupted()) {
                MiddlewareRequest request = MiddlewareQueue.take();
                request.dequeueNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());
                request.queueLength = MiddlewareQueue.getQueueLength();
                request.workerId = this.id;

                request.parse(numServers, readSharded);

                String response;

                switch (request.requestType) {
                    case "SET":
                        response = handleSetRequest(request);
                        break;
                    case "GET":
                        response = handleGetRequest(request);
                        break;
                    case "MULTI-GET":
                        if (this.readSharded){
                            response = handleMultiGetRequest(request);
                        } else {
                            response = handleGetRequest(request);
                        }
                        break;
                    default:
                        response = "";
                }

                request.connection.write(response);
                request.returnedToClientNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

                // Finished processing request therefore we print it and give the connection back into the client pool
                logger.trace(request.toString());
            }
            System.out.println("Thread out of while loop");
        } catch (InterruptedException e){
            Thread.currentThread().interrupt();
        } catch(Exception e){
            logger.error("Worker " + this.id + " " + e);
            e.printStackTrace();
        }
    }

    private String handleSetRequest(MiddlewareRequest request) throws IOException{

        // send all requests
        for (int i = 0; i < numServers; i++){
            Connection server = servers.getConnection(request.requestId + i);
            server.write(request.command);
            request.serverId = server.Id;
        }

        request.sentToServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

        // gather responses
        String[] responses = new String[numServers];
        for (int i = 0; i < numServers; i++){
            Connection server = servers.getConnection(request.requestId + i);
            responses[i] = server.read(readBuffer);
        }

        request.receivedFromServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());


        // parse responses
        boolean allAreStored = true;

        for (String response : responses){
            allAreStored = allAreStored && response.equals("STORED\r\n");
        }

        if (allAreStored){
            request.isSuccessful = true;
            return "STORED\r\n";
        } else {
            request.isSuccessful = false;
            return "NOT STORED\r\n";
        }
    }

    private String handleGetRequest(MiddlewareRequest request) throws IOException{
        Connection server = servers.getConnection(request.requestId);
        server.write(request.command);

        request.serverId = server.Id;
        request.sentToServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

        String response = server.read(readBuffer);

        request.receivedFromServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

        request.isSuccessful = !response.equals("END\r\n");
        request.numKeysReturned = request.isSuccessful ? 1 : 0;

        return response;

    }

    private String handleMultiGetRequest(MiddlewareRequest request) throws IOException{
        // send all requests
        for (int i = 0; i < request.commands.size(); i++){
            String command = request.commands.get(i);
            Connection server = servers.getConnection(request.requestId + i);
            server.write(command);
            request.serverId = server.Id;
        }

        request.sentToServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

        // gather responses
        String[] responses = new String[request.commands.size()];
        for (int i = 0; i < request.commands.size(); i++){
            Connection server = servers.getConnection(request.requestId + i);
            responses[i] = server.read(readBuffer);
        }

        request.receivedFromServerNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());

        // parse responses
        StringBuilder stringBuilder = new StringBuilder();
        for (String response : responses) {
            stringBuilder.append(response, 0, response.length() - 5);
        }
        stringBuilder.append("END\r\n");
        String response = stringBuilder.toString();

        request.isSuccessful = !response.equals("END\r\n");
        request.numKeysReturned = (response.split("\r\n").length-1)/2; // two lines per key returned

        return response;
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


