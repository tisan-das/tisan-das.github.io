---
published: false
---
One of the foundation problem of designing a distributed system is how to store some data over a distributed system. One basic approach is to share or duplicate all the data between the nodes. However the complexity arises when multiple nodes can operate independently, and in case some node goes down the complexity arises many folds. In this blogpost we will learn about Raft: one of the most commonly used coneseus algorithm. We would brifely touch about the generic replication technique on DB replication as well.

Each distributed system caters to large number of requests, which ultimately boils down to either read requests or write requests. The intended use of the write requests are to persist the data, so that at later point of time the same can be used. Filesystem and Database are most commonly used persistent storage, however database wins here majority of the time due to majority of the data can be thought of as transactional records, and databases provides a certain layer of reliablity and robustness over filesystem. Hence here we will mainly focus on the use of database.

Now, even though from the application perspective, the database interface layer points to a single database, however databases also consists of serveral nodes connected through network, and it's the responsibility of the distrbuted database to ensure data can be retrieved even if couple of nodes goes down. This where data replication among the nodes comes into the picture.

One of the most commonly used approach here to use a single leader replication, where the write operations are catered by the leader node only. As and when the write operations are done, they are replicated to the other nodes. There's two types of replication policy which can be used:
1. Synchonous replication: Wait for acknowledgement from the follower nodes first, before commiting data
2. Asynchronous replication: Trigger replication, however not to wait for acknowledgement from the follower nodes before commiting data



// Image for dataReplication




And depending upon the configuration, the read operations can be catered by the followers also.

### References:
1. https://www.geeksforgeeks.org/advantages-of-dbms-over-file-system/
1. https://towardsdatascience.com/database-replication-explained-5c76a200d8f3
2. https://towardsdatascience.com/raft-algorithm-explained-a7c856529f40
3. https://towardsdatascience.com/raft-algorithm-explained-2-30db4790cdef
