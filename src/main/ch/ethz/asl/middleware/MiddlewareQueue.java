package ch.ethz.asl.middleware;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

import ch.ethz.asl.middleware.utils.*;

public class MiddlewareQueue{

    private static BlockingQueue<MiddlewareRequest> queue = new LinkedBlockingQueue<MiddlewareRequest>();

    private MiddlewareQueue(){
        // prevent instantiation
    }

    public static void Add(MiddlewareRequest request) throws InterruptedException{
        queue.put(request);
    }

    public static synchronized MiddlewareRequest Take() throws InterruptedException{
        return queue.take();
    }
}