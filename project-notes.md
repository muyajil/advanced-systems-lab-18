# Project Description ASL Project 18

## General Notes
- [ ] Connections to client and servers must be kept open. That means we need to manage sockets ourselves
- [ ] Max data size is 4096B
- [ ] Based on the data size, number of keys and number of worker threads we can compute the needed memory to run the application. I think there will be more than enough memory to allocate large buffers for responses, maybe if we can preallocate and reuse them we can improve the performance.

## Memtier
- [ ] memtier just sends and reads random keys.
- [ ] The key space however is limited. It is expected we warm up the cached such that about all keys were written. Miss rates should be low.

## SET Operations
- [ ] Send to all memcached servers.
- [ ] First send to all, then read from all.
- [ ] If all servers respond STORED then we can return STORED to the client.
- [ ] If any of the servers do not respons with STORED we relay whatever the not matching response was. We can instantly return if one is not stored, since we can return any of the error messages.
- [ ] We can always directly return the memcached response.
- [ ] Do not retry setting the key

## GET Operations
- [ ] Middleware acts as a load balancer.
- [ ] Each request is forwarded to one server.
- [ ] Scheduling in Round Robin fashion
- [ ] No load dependent scheduling
- [ ] Answer of a GET can be just empty, then the key was evicted from the cache

## MULTI-GET Operations

 - [ ] If i remember correctly MGETs are just GETs with multiple keys.

### Non Sharded
- [ ] MGETs are treated the same way as GETs
- [ ] Up to 10 values in the same response
- [ ] We should know the data size since we set that in memtier. Can we set the buffer size for reading exactly at number of keys * data size?

### Sharded
- [ ] Split MGETs into multiple MGETs
- [ ] If there are 2 Keys not all servers get a request
- [ ] Middleware should first send all requests before attempting to read -> happens automatically if we use the command list. There is just an inner loop which only in the case of sharded MGETs has more than 1 iteration.
- [ ] After reading the responses we need to reassemble them to one response -> strip some stuff from beginning and end.

## Middleware

### Net Thread
- [ ] Accept incoming connections on some TCP port.
- [ ] Single net thread that listens to these incoming connections. Allocate a socket and hold that socket.
- [ ] Net thread also has to read from the sockets and add these requests to the request queue.
- [ ] Reads need to be non blocking, in case a client is still waiting for a response.

### Worker threads
- [ ] Worker threads need to dequeue requests from the request queue.
- [ ] Worker threads are in a thread pool
- [ ] Parameter for the size is given at startup time.
- [ ] A maximum of 128 threads need to be supported.
- [ ] A worker thread needs to handle all 3 mentioned types of requests.
- [ ] If the request is neither of these types the event needs to be recorded and the data discarded. I.e. do not crash on bad requests.
- [ ] Each thread has dedicated connections to all memcached servers. 
- [ ] These connections only close when the Middleware shuts down.
- [ ] The worker thread can answer the client directly, no need to involve the net thread -> client socket needs to be a part of the requeset. 
- [ ] After responding to a request the worker thread needs to keep track of the completed request objects. This can already be a string.

### Startup
- [ ] Middleware needs to parse command line arguments.
- [ ] Servers to connect to
- [ ] Number of Worker threads

### Shutdown
- [ ] The Middleware needs to be able to catch a kill from Linux to shutdown.
- [ ] The Middleware needs to print all of its statistics when exiting. 
- [ ] On shutdown the net thread gathers all the processed requests from the worker threads.
- [ ] The net thread then prints all the data of these request to STDOUT
- [ ] The output should be a csv that has a col for each measurement point.

## Instrumentation
- [ ] The Middleware needs to collect aggregate statistics per at most 5 seconds.
- [ ] We can just record each request. Then we have an even better resolution.
- [ ] Statistics needed:
    - [ ] Average Throughput
    - [ ] Average Queue length
    - [ ] Average Waiting time in Queue
    - [ ] Average service time of the memcached servers
    - [ ] Number of GET, SET, and MGET operations
    - [ ] Cache miss ratio
    - [ ] Any error messages that occured during the experiment.
- [ ] Measurements for these statistics per request:
    - [ ] Sequence Number
    - [ ] Receive timestamp in net thread
    - [ ] Enqueue timestamp in net thread
    - [ ] Queue Length at enqueue in net thread
    - [ ] Dequeue timestamp in worker
    - [ ] Queue Length at dequeue in worker
    - [ ] Send timestamp to memcached (or first send timestamp for sharded MGETs) in worker
    - [ ] Received timestamp from memcached (or last receive timestamp for sharded MGETs) in worker
    - [ ] Send timestamp to client
    - [ ] Response from server (HIT/MISS, STORED/ERROR)
    - [ ] Any exception in handling the request
- [ ] We can implement a ToString method for the RequestDataSet to generate a csv row.
- [ ] Need to be able to produce a histogram of response times in 0.1sec buckets.
- [ ] Measure other stuff as well such as ping times etc.
