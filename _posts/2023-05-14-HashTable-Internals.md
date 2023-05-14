---
layout: post
title: Introduction to System Design
published: true
---

Hash table is one of the most important data structure, which gets used for fast insertion and retrieval of key-value pairs. We get introduced to this Hash data structure pretty early in our engineering journey, however, the internal designing of the hash table is quite entangled with multiple designs to choose from depending upon application specific behaviour. The full extent of the hash table implementation maybe grasped by the fact that even the programming language runtime also depends on it, as it's quite extensibly used for classes and memeber attribute lookup for languages supporting OOPS, and variable lookup table in case of procedural languages. In this blog post, we would explore the fundamental ceoncepts behind hash table, how collisions are resolved, performance and certain optimizations.

### Ideas:
##### Idea 01: Application key to hash key [0,N):
We can't put anything as key in hash table. It's limited to a set of specific set of types eg. string, int, tuple etc. We can also use custom types as keys if they implements a hash function that provides an integer corresponding to the custom type or object. For some native types, the hash function is implicitly defined.
##### Idea 02: Mapping hash key in smaller range:
The hash table size is generally quite smaller compared to the range of the application key, which requires an additional hash to reduce the range to distrbute over the holding array. As and when the holding array gets populated, the holding array may need to be resized, and redistrbution of the application key needs to be done.

### Collision in Hash Table:
In case different objects maps to the same application key, or different application key gets mapped to the same hash table key, the collision needs to be resolved. There's two different types of collision resolution: Chainigin and Open adressing

##### Chaining:
The collided keys are placed in a data structure pointed by the hash table key. The basic implementation is to form a chain of keys with the use of linked list that mapped to the same hash table key.

Chaining with linked list:
- The hash table is an array of pointer to linked list. Each slot of array contains a pointer to the head of the linked list
- Each node of the list contains pointer to the actual data (key and the value) and a pointer to the next node in the list

Chaining with other data structures:
- Self-balancing binary tree: Insertion and lookup is O(h)
- Useful when collision rate is high, and cant resize the holding table


##### Open adressing:
Instead of using some auxilary data structure like chaining, utilize the empty slots when the keys collided, find a way to look for the available slots in a deterministic way. 
Probing: function for finding the next available slot. A good probing function should generate permutations to cover the entire space eventually.

For adding or lookup, we need to continously probe until a empty slot is encountered or all the slots are checked. Hence while deleting a key, it's needed to be a soft delete, otherwise the looup would miss existing keys.

Linear probing:
- Search linearly from the hash index until the end of the table, then wrap from the start
- If empty slot, then the key is not present
- Advantage: localized access: OS caches the whole block, hence neighbouring element access becomes very fast
- Challenges:
    - Bad hash function would make linear probing a full table search
    - Linear procing suffers from clustered collision

Quadratic probing:
- Clustered and cascaded collisions are reduced as collided keys are placed further away from each other
- offset is increased quadtratically

Double hashing:
- Use a secondary hash function to offset collision 
- Unlike quadratic probing, offset for double hasing follows a linear pattern
- The secondary hash function should never return 0 and should cycle through the entire table, and should be fairly simple to compute



### Resizing hash table:
Aggresive resizing would lead to too frequent resize, which is a time consuming process, and can't also be too linent with resizing, as that would degrate performance. General hands-of-rule is to expand the holding array once load factor is increased to 0.5 and shrink it once load factor is reduced to 0.125.

Also one more point to be noted that having the hash table sized to be exponent of 2, as the hash functions extensivly relies upon mod operation. And the mod operation is compute heavy if division operation is used. However with bit manipulation, AND operation with (2^n-1) would also result into equivalent mod operation.


### References:
1. [Hash Table Internals](https://www.youtube.com/playlist?list=PLsdq-3Z1EPT2UnueESBLReaVSLIo_BuAc)
