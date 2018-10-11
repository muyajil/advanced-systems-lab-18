package ch.ethz.asl.middleware.utils;

import java.io.IOException;
import java.util.ArrayList;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;


public class ConnectionManager{
    
    private int nextId;
    private boolean isBlocking;
    private BlockingQueue<Connection> Connections;

    public ConnectionManager(boolean isBlocking){
        nextId = 0;
        this.isBlocking = isBlocking;
        Connections = new LinkedBlockingQueue<Connection>();
    }

    public synchronized void addConnection(Connection connection) throws IOException{
        connection.Id = nextId;
        connection.ConfigureBlocking(isBlocking);
        nextId += 1;
        Connections.add(connection);
    }

    public synchronized Connection popConnection(){
        return Connections.poll();
    }

    public synchronized void putConnection(Connection connection){
        Connections.add(connection);
    }
}