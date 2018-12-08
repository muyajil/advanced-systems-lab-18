package ch.ethz.asl.middleware.utils;

import java.nio.channels.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.io.IOException;
import java.net.*;

public class Connection{

    public SocketChannel socketChannel;
    public int Id;
    private boolean isBlocking;

    public Connection(SocketChannel socketChannel){
        this.socketChannel = socketChannel;
    }

    public void configureBlocking(boolean isBlocking) throws IOException{
        socketChannel.configureBlocking(isBlocking);
        this.isBlocking = isBlocking;
    }

    public String read(ByteBuffer buffer) throws IOException{
        if(this.isBlocking){
            return readBlocking(buffer);
        }
        return readNonBlocking(buffer);
    }

    private String readBlocking(ByteBuffer buffer) throws IOException{
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

    private String readNonBlocking(ByteBuffer buffer) throws IOException{
        buffer.clear();
        int totalBytesRead = socketChannel.read(buffer);

        while(true){
            if(totalBytesRead <= 0){
                return "";
            }

            totalBytesRead += socketChannel.read(buffer);

            if(buffer.array()[totalBytesRead - 1] == 10){
                break;
            }
        }

        return new String(buffer.array()).substring(0, totalBytesRead);
    }

    public void write(String message, ByteBuffer buffer) throws IOException{
        buffer.clear();
        buffer.put(message.getBytes());
        buffer.flip();
        while(buffer.hasRemaining()){
            socketChannel.write(buffer);
        }
        buffer.flip();
    }
}