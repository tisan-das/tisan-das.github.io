---
published: true
---
One of the foundation problem of designing a distributed system is how to store some data over a distributed system. One basic approach is to share or duplicate all the data between the nodes. However the complexity arises when multiple nodes can operate independently, and in case some node goes down the complexity arises many folds. In this blogpost we will learn about Raft: one of the most commonly used coneseus algorithm. We would brifely touch about the generic replication technique on DB replication as well.

Each distributed system caters to large number of requests, which ultimately boils down to either read requests or write requests. The intended use of the write requests are to persist the data, so that at later point of time the same can be used. Filesystem and Database are most commonly used persistent storage, however database wins here majority of the time due to majority of the data can be thought of as transactional records, and databases provides a certain layer of reliablity and robustness over filesystem. Hence here we will mainly focus on the use of database.

Now, even though from the application perspective, the database interface layer points to a single database, however databases also consists of serveral nodes connected through network, and it's the responsibility of the distrbuted database to ensure data can be retrieved even if couple of nodes goes down. This where data replication among the nodes comes into the picture.

One of the most commonly used approach here to use a single leader replication, where the write operations are catered by the leader node only. As and when the write operations are done, they are replicated to the other nodes. And depending upon the configuration, the read operations can be catered by the followers also. There's two types of replication policy which can be used:
1. Synchonous replication: Wait for acknowledgement from the follower nodes first, before commiting data
2. Asynchronous replication: Trigger replication, however not to wait for acknowledgement from the follower nodes before commiting data

// Image for dataReplication

The asynchronous replication technique has one drawback: the consistency for read after write requests can't be guranteed. 

// Image for async read issue

There are cetain workarounds to this, for example storing updated timestamp on client side to read the updated after the specific timestamp, or by means of sticky routing, however none of them still gurantees strong consistency. So the distributed systems not requiring strong consistency can absolutely take this approach. However based on CAP theorem, which we would explore in a later post, the CP and CA systems wouldn't be able to rely on async data replication technique.


Single leader replication failure contains two major drawbacks:
1. How to handle a node going down: If a node goes down, and joins back again, how to have the updated data replicated?
2. What if a leader goes down: How to elect a new leader? Also would there be a possibility of two leaders operating simultaneosly?

This is where a consensus algorithm like Raft comes into the picture. Consesus algorithm provides the procedure to not only to elect a leader in case the current leader goes down, it also provides a way to ensure that the 

The primary concept behind the Raft algorithm is that each node can either be a leader, follower or at the election time, a candidate:

// Image transition

The transition rules are pretty much self evident. When the system is initialized, an external force is needed to select the initial leader. However once the leader is elected, it remains leader until it goes down, or it gets disconnected from majority of the servers. The leader node periodically sends a heartbeat signal to the rest of the nodes. 

If one of the node sees that it's not recieving any hearbeat from the leader nodes, it becomes a candidate node, proposes itself to be a leader node, and broadcasts a voting request to other node. Now, there's a concept of term number, an increasing number to denote the term for which election is going on, and when a leader is selected it uses the term number to replicate and store the logs in persistence storage. Raft algorithm only allows append operation on logs. Hence when a leader is selected, it's assumed all the logs till the previous term is already commited, and requires no further intervention.

Now, leader selection is a vital process. To ensure that not all the nodes becomes candidate node at the same time, a randomized election timeout is used. Also there's one more vital issue for the leader election. The leader node should have the all the entries updated, hence before casting vote, the followe node verifies whether the candidate node is up-to-date both interms of term number, and the log index of the previous term. Also, a follower node can casts it's vote for only one node given a term. The candidate node becomes the leader if it has got the votes for the majority of the nodes.


// Image for request votes



The appendLog is the second type of message broadcasted. Only the leader node can broadcast this type of message. Now because only append operation is allowed on the logs i.e. the data modification, the out of sync appending isn't allowed. It's always assumed that logs are appended in the same order leader is having. In order to enforce this prevLogIndex value is maintained as well as prevLogTerm, which denotes the index and the term of the latest updated log. And in case the node finds some log which are out-of-sync, i.e. more recent logs, the node discards them and waits to get the intended logs. These arguments are sent by the leader node, and the follower verifies whether need to append the logs, or reject and wait for older messages to get appened, or in case of conflicting entry with the leader node specific to the current term, then to update it. Now from the above discussion, it's clear that the leader node have to broadcast the entries multiple times, and is generally is generally broadcasted periodically.

Following are the arguments to the appendEntry/appendLog command:

// Image of appendLog

Once the leader gets acknowledgement from majority of the node for a specific logIndex, it updates the commitIndex, denoting that the logs or transactions till that index is already committed. This is a way to let the higher level application know that the transaction is already committed. Now in case the leader goes down abruptly, the client will know that the rest of the data isn't committed to the system.


It's to be noted that, there's still a possibility of having multiple leader nodes, in case the earlier leader is partitioned, and is disconnected from rest of the nodes, due to which it still remains an isolated node, and isn't updated about the latest term. However in this case the obsolete leader will not have acknowledgement from the majority of the nodes, hence commit willn't occur. There are also some improvement proposed to top of Raft, by using a commit timeout, where in case there's no further commit happpens within a stipulated time, then it's assumed that the leader is disconnected, and goes back to the follower state, to let another round of election take place.

As soon as this node gets connected to the current leader node, it understands that the it's own term is a of preeceding term, and hence relegates to the follower state. In this case the logs from the earlier terms can be lost from this particular node, however as the data is already committed to the majority of the nodes, and each read also needs the majority consensus, this scenario wouldn't cause any issue.



### References:
1. https://www.geeksforgeeks.org/advantages-of-dbms-over-file-system/
1. https://towardsdatascience.com/database-replication-explained-5c76a200d8f3
3. https://www.youtube.com/watch?v=uXEYuDwm7e4&list=PLeKd45zvjcDFUEv_ohr_HdUFe97RItdiB&index=18
2. https://towardsdatascience.com/raft-algorithm-explained-a7c856529f40
3. https://towardsdatascience.com/raft-algorithm-explained-2-30db4790cdef
6. Improving Raft When There Are Failures https://tik-db.ee.ethz.ch/file/17210168ce3be9d0e6a5e3f846fb1b29/Improving_RAFT_When_There_Are_Failures.pdf
