package ch.ethz.asl.middleware;

import java.util.*;

public class Middleware implements Runnable{

    public Middleware(
        String ip,
        int port,
        List<String> mcAddresses,
        int numThreads,
        boolean readSharded
    ){

    }

    public void run(){
        System.out.println("Hello World!");
    }
}