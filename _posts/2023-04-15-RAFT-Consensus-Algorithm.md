---
published: false
---
One of the foundation problem of designing a distributed system is how to store some data over a distributed system. One basic approach is to share or duplicate all the data between the nodes. However the complexity arises when multiple nodes can operate independently, and in case some node goes down the complexity arises many folds. In this blogpost we will learn about Raft: one of the most commonly used coneseus algorithm. We would brifely touch about the  


It's to be noted that not all the nodes are available all the time. Hence even through a basic

There's some way to handle these kind of issues, one major approach is through the use of service registry, which we would explore on a different post. However before going there we would first explore on Raft, a well known consensus algorithm.