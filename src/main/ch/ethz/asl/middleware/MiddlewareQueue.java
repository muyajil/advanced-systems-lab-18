package ch.ethz.asl.middleware;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import ch.ethz.asl.middleware.utils.*;

public class MiddlewareQueue{

    private static BlockingQueue<MiddlewareRequest> queue = new LinkedBlockingQueue<MiddlewareRequest>();

    private MiddlewareQueue(){
        // prevent instantiation
    }

    public static void add(MiddlewareRequest request) throws InterruptedException{
        queue.put(request);
    }

    public static synchronized MiddlewareRequest take() throws InterruptedException{
        return queue.take();
    }

    public static int getQueueLength(){
        return queue.size();
    }
}