---
layout: post
title: Introduction to NoSQL Databases
published: true
---

Databases are one of the most used components of any web service. It's safe to say that all the web services serve the requests by processing the data fetched from the databases, and by storing the updated information on there. Even though it's used as persistent storage, the primary benefit of a database lies in the efficient retrieval of the stored data. With the current generation of databases, they can be broadly categorized into RDBMS and NoSQL. Here in this blog post, we will mainly try to get an overview of the NoSQL database, how it started getting popularity, its use case, and its drawbacks. So off we go...


### History:
From the '90s, with the advent of databases, relational databases started to gain popularity. The primary reason behind that was the relational nature, where the data is stored in a tabular fashion, and the relationship is maintained with the help of referential integrity in the form of the foreign key. The major benefit of the relational database lies in the support of transactions, where a bunch of statements are grouped to form a transaction, and are provided atomicity and isolation support. The transactions and relational nature also help business reporting much easier, where data can be captured across different relations, which is also consistent. **Integration of different applications over the same database** is one of the major deciding factors for adopting relational databases.

However, with the advent of more web services, there are some anomalies found with the way data is stored and how the same data is represented over the UI. With relational databases, the same data is scattered across different tables and is stitched through the referential integrity, causing **Impedance Mismatch**. To build such a response model, multiple queries are needed to be executed. 

There's another disadvantage with relation database. The relational databases don't scale up very well vertically. To scale up the relational databases, it's generally recommended to perform a horizontal scale, before performing a vertical scale-up, as it's difficult to maintain the same relations over a cluster of nodes. However with the advent of web services, major web platforms introduced a concept of using clusters of nodes consisting of commodity-level hardware to store the data, and thus initiated to exploration of the database architecture to support this type of computation network for specific use cases.

The majority of the prominent RDBMS organizations tried to come up with solutions, however, a subset of databases became more popular, as they were able to leverage the new type of computational network by reducing the usage of relations or discarding it altogether. These types of databases were termed NoSQL, just to denote the contrast with RDBMS.

### Types:
1. Key-value
2. Document data
3. Column family database: One entry is mapped to columns of related data. 
4. Graph database: Helps with granular relations

The first three types come under aggregate-oriented databases, as they're generally aggregated over certain key or document ID or column index.
There's a general consensus that only the RDBMS provides support for ACID properties, but not the NoSQL ones. Even though it's true, however, it's to be noted that certain NoSQL databases also support the same ACID properties to a certain extent, which is generally good enough for the majority of the applications. For example, aggregate-oriented databases provide support for atomicity in the scope of their aggregate attributes. However, if there's a need to slice and dice the data, then aggregate-oriented databases are at a disadvantage, as the need to scan through the whole database to capture such info, graph database comes to the rescue in these cases.


### Future Study:
- Implementation of NoSQL database, especially the graph database


### References:
1. [Introduction to NoSQL by Martin Fowler](https://www.youtube.com/watch?v=qI_g07C_Q5I)

