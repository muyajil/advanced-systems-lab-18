package ch.ethz.asl.middleware;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;

import java.util.*;

import ch.ethz.asl.middleware.utils.*;

public class Middleware implements Runnable{

    private String ipAddress;
    private int listenPort;
    private boolean readSharded;
    private List<Thread> workerThreads;
    private int requestId = 0;
    private ConnectionManager clients = new ConnectionManager(false);

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

    @Override
    public void run(){
        try{

            ServerSocketChannel listeningSocket = getListeningSocket();

            while(true){
                SocketChannel clientSocket = listeningSocket.accept();
                if (clientSocket != null){
                    clients.addConnection(new Connection(clientSocket));
                }

                for (Connection connection : clients.Connections){
                    break;
                }
            }

        } catch(Exception e){
            e.printStackTrace(System.out);
        }
    }

    private ServerSocketChannel getListeningSocket() throws IOException{
        ServerSocketChannel listeningSocket = ServerSocketChannel.open();
        listeningSocket.socket().bind(new InetSocketAddress(listenPort));
        listeningSocket.configureBlocking(false);
        return listeningSocket;
    }
}