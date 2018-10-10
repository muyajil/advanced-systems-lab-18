package ch.ethz.asl.middleware;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

import ch.ethz.asl.middleware.utils.*;

public class MiddlewareQueue{

    private static BlockingQueue<MiddlewareRequest> queue = new LinkedBlockingQueue();
    private static Lock lock = new ReentrantLock(true);

    private MiddlewareQueue(){
        // prevent instantiation
    }

    public static void Add(MiddlewareRequest request) throws InterruptedException{
        queue.put(request);
    }

    public static MiddlewareRequest Take() throws InterruptedException{
        lock.lockInterruptibly();
        try {
            return queue.take();
        } finally {
            lock.unlock();
        }
    }
}