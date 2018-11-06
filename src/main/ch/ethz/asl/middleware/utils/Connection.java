package ch.ethz.asl.middleware.utils;

import java.nio.channels.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.io.IOException;
import java.net.*;

public class Connection{

    private ByteBuffer buffer;
    private SocketChannel socketChannel;
    public int Id;
    private boolean isBlocking;

    public Connection(SocketChannel socketChannel){
        this.socketChannel = socketChannel;
        this.buffer = ByteBuffer.allocate(51200); // 50kb is enough to cover all cases
    }

    public void configureBlocking(boolean isBlocking) throws IOException{
        socketChannel.configureBlocking(isBlocking);
        this.isBlocking = isBlocking;
    }

    public synchronized String read() throws IOException{
        if(this.isBlocking){
            return readBlocking();
        }
        return readNonBlocking();
    }

    private String readBlocking() throws IOException{
        buffer.clear();
        int totalBytesRead = 0;

        while(true){
            totalBytesRead += socketChannel.read(buffer);
            if(buffer.array()[totalBytesRead - 1] == 10){
                break;
            }
        }

        return new String(buffer.array()).substring(0, totalBytesRead);
    }

    private String readNonBlocking() throws IOException{
        buffer.clear();
        int totalBytesRead = socketChannel.read(buffer);

        while(true){
            totalBytesRead += socketChannel.read(buffer);

            if(totalBytesRead <= 0){
                return "";
            }

            if(buffer.array()[totalBytesRead - 1] == 10){
                break;
            }
        }

        return new String(buffer.array()).substring(0, totalBytesRead);
    }

    public synchronized void write(String message) throws IOException{
        buffer.clear();
        buffer.put(message.getBytes());
        buffer.flip();
        while(buffer.hasRemaining()){
            socketChannel.write(buffer);
        }
        buffer.flip();
    }
}