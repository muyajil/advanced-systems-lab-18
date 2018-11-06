package ch.ethz.asl.middleware;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.*;

import ch.ethz.asl.middleware.utils.Connection;
import ch.ethz.asl.middleware.utils.ConnectionManager;
import ch.ethz.asl.middleware.utils.MiddlewareRequest;
import ch.ethz.asl.middleware.Worker;
import ch.ethz.asl.middleware.MiddlewareQueue;

public class Middleware implements Runnable{

    private String ipAddress;
    private int listenPort;
    private boolean readSharded;
    private List<Thread> workers;
    private int nextRequestId = 0;
    private static final Logger logger = LogManager.getLogger("Middleware");
    private boolean isShutdown;

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
        logger.trace(MiddlewareRequest.getHeader());

        Runtime.getRuntime().addShutdownHook(new Thread(this::shutdownWorkers));
        this.workers = getRunningWorkers(numThreads, mcAddresses, readSharded);
    }

    @Override
    public void run(){
        try{
            ServerSocketChannel listeningSocket = getListeningSocket();

            while(!isShutdown){
                SocketChannel clientSocket = listeningSocket.accept();
                if (clientSocket != null){
                    Clients.addConnection(new Connection(clientSocket));
                }

                Connection client = Clients.popConnection();
                if (client != null){
                    String command = client.read();
                    if (!command.equals("")){
                        MiddlewareQueue.add(new MiddlewareRequest(){{
                            connection = client;
                            commands = new ArrayList<>(){{
                                add(command);
                            }};
                            requestId = nextRequestId;
                            clientId = client.Id;
                            enqueueMilli = System.currentTimeMillis();
                            enqueueNano = System.nanoTime();
                        }});
                        nextRequestId++;
                    } else {
                        Clients.putConnection(client);
                    }
                }
            }
            LogManager.shutdown();

        } catch(Exception e){
            logger.error("Middleware: " + e);
        }
    }

    private ServerSocketChannel getListeningSocket() throws IOException{
        ServerSocketChannel listeningSocket = ServerSocketChannel.open();
        listeningSocket.socket().bind(new InetSocketAddress(listenPort));
        listeningSocket.configureBlocking(false);
        return listeningSocket;
    }

    private List<Thread> getRunningWorkers(int numWorkers, List<String> mcAddresses, boolean readSharded){
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < numWorkers; i++){
            Thread worker = new Thread(new Worker(mcAddresses, readSharded, i));
            worker.start();
            workers.add(worker);
        }
        
        return workers;
    }

    private void shutdownWorkers(){
        for (Thread worker : this.workers){
            try {
                worker.interrupt();
                worker.join();
                isShutdown = true;
            } catch (InterruptedException e) {
                logger.error(e);
            }
        }
    }
}