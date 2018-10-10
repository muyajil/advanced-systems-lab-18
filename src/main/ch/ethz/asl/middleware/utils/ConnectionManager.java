package ch.ethz.asl.middleware.utils;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class ConnectionManager{
    
    private int nextId;
    private boolean isBlocking;
    public List<Connection> Connections;

    public ConnectionManager(boolean isBlocking){
        nextId = 0;
        this.isBlocking = isBlocking;
        Connections = new ArrayList<Connection>();
    }

    public void addConnection(Connection connection) throws IOException{
        connection.Id = nextId;
        connection.ConfigureBlocking(isBlocking);
        nextId += 1;
        Connections.add(connection);
    }
}