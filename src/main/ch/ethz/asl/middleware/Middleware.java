package ch.ethz.asl.middleware;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.util.*;

import ch.ethz.asl.middleware.utils.Connection;
import ch.ethz.asl.middleware.utils.MiddlewareRequest;

public class Middleware implements Runnable{

    private int listenPort;
    private String myIp;
    private List<Thread> workers;
    private int nextRequestId = 0;
    private static final Logger logger = LogManager.getLogger("Middleware");
    private boolean isShutdown;
    private Selector selector;
    private int nextClientId = 0;
    private ByteBuffer readBuffer;

    public Middleware(
        String ipAddress,
        int port,
        List<String> mcAddresses,
        int numThreads,
        boolean readSharded
    ) throws IOException {
        this.listenPort = port;
        this.myIp = ipAddress;
        logger.trace(MiddlewareRequest.getHeader());
        MiddlewareRequest.serverStartMilli = System.currentTimeMillis();
        MiddlewareRequest.serverStartNano = System.nanoTime();

        Runtime.getRuntime().addShutdownHook(new Thread(this::shutdownWorkers));
        this.selector = Selector.open();
        this.workers = getRunningWorkers(numThreads, mcAddresses, readSharded);
        this.readBuffer = ByteBuffer.allocate(51200);
    }

    @Override
    public void run(){
        try{
            initListeningSocket();

            while(!isShutdown){

                if (selector.select() <= 0) {
                    continue;
                }

                Iterator<SelectionKey> selectedKeys = selector.selectedKeys().iterator();
                while (selectedKeys.hasNext()){
                    SelectionKey key = selectedKeys.next();
                    selectedKeys.remove();
                    if (key.isAcceptable()){
                        registerNewClient(key);
                    }
                    if (key.isReadable()){
                        handleNewRequest(key);
                    }
                }
            }
            LogManager.shutdown();

        } catch(Exception e){
            logger.error("Middleware: " + e);
        }
    }

    private void handleNewRequest(SelectionKey key) throws IOException, InterruptedException{
        long startReceiving = MiddlewareRequest.getRealTimestamp(System.nanoTime());
        Connection client = (Connection) key.attachment();
        String cmd = client.read(readBuffer);
        if (!cmd.equals("")) {
            MiddlewareQueue.add(new MiddlewareRequest() {{
                connection = client;
                command = cmd;
                requestId = nextRequestId;
                clientId = client.Id;
                enqueueNano = MiddlewareRequest.getRealTimestamp(System.nanoTime());
                startReceivingNano = startReceiving;
            }});
            nextRequestId++;
        }
    }

    private void registerNewClient(SelectionKey key) throws IOException{
        ServerSocketChannel listeningSocket = (ServerSocketChannel) key.channel();
        SocketChannel clientSocket = listeningSocket.accept();
        Connection client = new Connection(clientSocket);
        client.Id = nextClientId;
        nextClientId += 1;
        client.configureBlocking(false);
        client.socketChannel.register(selector, SelectionKey.OP_READ, client);
    }

    private void initListeningSocket() throws IOException{
        ServerSocketChannel listeningSocket = ServerSocketChannel.open();
        listeningSocket.configureBlocking(false);
        listeningSocket.socket().bind(new InetSocketAddress(InetAddress.getByName(this.myIp), this.listenPort));
        listeningSocket.register(selector, SelectionKey.OP_ACCEPT);
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
            worker.interrupt();
        }

        for (Thread worker : this.workers){
            try {
                worker.join();
            } catch (InterruptedException e) {
                logger.error(e);
                Thread.currentThread().interrupt();
            }
        }
        isShutdown = true;
    }
}