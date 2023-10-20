---
layout: post
title: CAP Theorem
published: true
---


CAP Theorem is an interesting theorem proposed by Eric Brewer, which states that any distributed system can provide only two of the following three guarantees:
1. **Consistency:** Every read request should return the most recent write or an error.
Please note that there's a subtle difference in the term consistency as defined in the CAP theorem and ACID properties of RDBMS. In the case of ACID properties of RDBMS, consistency means the integrity of data should be maintained before and after transactions. There shouldn't be new data created. 
2. **Availability:** Every request receives a non-error response, however, the response doesn't guarantee the most recent data
3. **Partition Tolerance:** The system continues to operate despite an arbitrary number of messages getting dropped or delayed by the network between the nodes

In case there's a network partition, a distributed system can pick up either to be available or consistent. In case some partition failure occurs, the distributed system can opt to cancel all the incoming requests to provide consistent data, however, that would reduce the availability of the system. In case the distributed system opts for availability in case of a network partition, then the response sent might not correspond to the most recent write operation and, thus would have to part off with consistency.

It's to be noted that a distributed system may neither be consistent nor available in case partition occurs. The theorem suggests it can only opt for either one of consistency and availability.

Google released Spanner as a globally distributed database, which is claimed to achieve both consistency and availability. At first glance, it seems like the limitation defined by the CAP theorem is broken. However, Spanner being an RDBMS always needs to prioritize consistency over availability if the need arises. The way "effective CA" is achieved here is through using highly optimized hardware to ensure network partitioning becomes a rare event. Due to these operational improvements, in practice, the network partition is greatly limited, and the users can assume it as a "CA" system.


### To be explored:
- Internals of Cloud Spanner DB


### References:
1. [CAP Theorem](https://en.wikipedia.org/wiki/CAP_theorem)
2. [Cloud Snapper with CAP THeorem](https://cloud.google.com/blog/products/databases/inside-cloud-spanner-and-the-cap-theorem)
