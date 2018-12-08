package ch.ethz.asl.middleware.utils;

import java.io.IOException;


public class ConnectionManager{
    
    private int nextId;
    private boolean isBlocking;
    private Connection[] Connections;
    private int numServers;

    public ConnectionManager(boolean isBlocking, int numServers) {
        nextId = 0;
        this.isBlocking = isBlocking;
        Connections = new Connection[numServers];
        this.numServers = numServers;
    }

    public void addConnection(Connection connection) throws IOException{
        connection.Id = nextId;
        connection.configureBlocking(isBlocking);
        nextId += 1;
        Connections[connection.Id] = connection;
    }

    public Connection getConnection(int requestId){
        return Connections[requestId % numServers];
    }
}