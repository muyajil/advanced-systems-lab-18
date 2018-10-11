package ch.ethz.asl.middleware;

import ch.ethz.asl.middleware.utils.ConnectionManager;
import ch.ethz.asl.middleware.utils.Connection;
import java.io.IOException;

public class Clients{

    private static ConnectionManager connectionManager = new ConnectionManager(false);

    private Clients(){
        // prevent instantiation
    }

    public static synchronized void addConnection(Connection connection) throws IOException{
        connectionManager.addConnection(connection);
    }

    public static synchronized void putConnection(Connection connection) throws IOException{
        connectionManager.putConnection(connection);
    }

    public static synchronized Connection popConnection() throws IOException{
        return connectionManager.popConnection();
    } 
}