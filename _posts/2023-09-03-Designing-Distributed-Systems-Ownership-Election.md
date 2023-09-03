---
layout: post
title: Designing Distributed Systems - Ownership Election
published: true
---


In the last couple of blog posts, we've explored serving patterns, where distributing requests in terms of requests per second, or the data size getting loaded, or the time to process. Here in this blog post, we would explore scaling in terms of assignments, to determine which task owns a specific resource. For a single application, well-established in-process lock to ensure only one actor is owning a resource at a particular moment, however this becomes complicated in distributed systems due to inherent nature of such systems. In distributed system, where multiple server can access same resource simultaneously, in certain scenarios there's a need to determine which one owns the resource, and can perform restrictive operations without hinderance of other nodes.

##### Determining the need of master election:
Before going on the discussion of how ownership can be established, it's better to look into whether the application ever needs to consider this itself. For majority of the applications, having only one instance is sufficient. And even if the instance crashed, the container orchestrator handles the failure in following way:
1. Container Crash: Container is restarted automatically. Consider, each day we can observe on container crash and restart takes couple of seconds to up the service, it corresponds to 3-nines to 4-nines (3600*24-5)/(3600*24)=99.99% .
2. Container Hung: Container is restarted if container hung state is detected by the health check. Similar downtime would also be there whenever a new software patch is rolled out. The availability would follow the same 3-nines to 4-nines just like above
3. Node Failure: Container is moved to a different node. And in case a new node is supposed to spawned, it generally take couple of mins. Even if considering we can observe node failure each day, the service uptime is around 2-nines (3600*24-300)/(3600*24)=99.65%

So from the above discussion it's evident that, only in certain scenarios where the service needs to be available ranging from 3-nines to 4-nines as a critical component, only in such systems, we would need to introduce replica, where only one replica can be the designated owner of the resource.

##### Basics of master election:
There's two different ways to implement master election:
1. Utilize distributed consensus algorithms like Paxos or RAFT. However using the algorithms would inject more complexity to the application core logic.
2. Majority of the key-value store already implemented such consensus algorithms, and provides the abstractions needed to build more complicated locking and ownership election. The compare-and-swap operation atomically write a new value if the existing value matches with the exptected value. If the key-value doesn't match with the expected value then this function returns false, and if value doesn't exists and expected value is not null, then returns error. The time-to-live, TTL, allows the key to expire. With this cokmpare-and-swap operation along with TTL provides sufficient mechansim to implement a varity of distributed synchronization methodlogies. 

Many key value stores let us watch for changes instaed of polling.

TTL is helpful in scenarios where a process has obtained lock, however got crashed before releasing it. Also it needs to be ensured that any processing doesn't take more time than the TTL. Otherwise there's a possibility of lock getting expired before processing is completed, and violating the mutex ownership. Key-value stores generally aloso provide support for watchdog, which is used to keep looking for changes in a key, the same can be utilized to terminate a worker in case TTL is expires before unlock is invoked. However depending upon the key-value store, watchdog can take some time to perform these operation.


However still, there's a scope of issue:
```
1. Process-1 obtains the lock with TTL t.
2. Process-1 runs really slowly for some reason, for longer than t.
3. The lock expires.
4. Process-2 acquires the lock, since Process-1 has lost it due to TTL.
5. Process-1 finishes and calls unlock.
6. Process-3 acquires the lock.
```
At this point, Process-1 believes that it has unlocked the lock that it held at the beginning; it doesn’t understand that it has actually lost the lock due to TTL, and in fact unlocked the lock held by Process-2. Then Process-3 comes along and also grabs the lock. Now both Process-2 and Process-3 both believe they own the lock.

##### Implementing ownership:
Locks are great on establishing ownership for a short duration, however sometimes a process needs to take ownership of the resource for the whole time that process is running.
One obvious way would be to use a very long TTL, like a week or more, however it has got significant downside that if the current owner faults, then the next owner would be selected for a long time. Hence the concept of renewable lock, where the lock is renewed periodically by the owner.

```go
func (Lock l) renew() boolean {
    locked, _ = compareAndSwap(l.lockName, "1", "1", l.version, ttl)
    return locked
}

for {
    if !l.renew() {
        handleLockLost()
    }
    sleep(ttl/2)
}
```

The lock is supposed to be renewed every ttl/2 seconds, and need to implement ```handlerLockLost()``` method which terminates all activity related to lock, or simply it can terminate the application also, which would then be restarted by container orchestrator.

Even with all of the locking mechanisms we have described, it is still possible for two replicas to simultaneously believe they hold the lock for a very brief period of time. To understand how this can happen, imagine that the original lock holder becomes so overwhelmed that its processor stops running for minutes at a time. This can happen on extremely overscheduled machines. So it's better to double check that the process has still got the lock:

```go
func (Lock l) isLocked() boolean {
    return l.locked && l.lockTime + 0.75 * l.ttl > now()
}
```

The following is directly taken from the book mentioned:
To add one final further complicating wrinkle, it’s always possible that ownership could be obtained, lost, and then re-obtained by the system, which could actually cause a request to succeed when it should actually be rejected. To understand how this is possible, consider the following sequence of events:
1. Shard-1 obtains ownership to become master.
2. Shard-1 sends a request R1 as master at time T1.
3. The network hiccups and delivery of R1 is delayed.
4. Shard-1 fails TTL because of the network and loses lock to Shard-2.
5. Shard-2 becomes master and sends a request R2 at time T2.
6. Request R2 is received and processed.
7. Shard-2 crashes and loses ownership back to Shard-1.
8. Request R1 finally arrives, and Shard-1 is the current master, so it is accepted, but
this is bad because R2 has already been processed.

Such sequence of events seem byzantine, but in reality, in any large system they occur with disturbing frequency. Fortunately, this is similar to the case described previously, which we resolved with the resource version in etcd. We can do the same thing here. In addition to storing the name of the current owner in etcd, we also send the resource version along with each request. So in the previous example, R1 becomes (R1, Version1)


### TODO:
- Explore on implementation
- Whether well-known DBs provide support on locking
- Explore on byzantine issues



### References:
1. Designing Distributed Systems: Patterns & Paradigms for Scalable, Reliable Services
