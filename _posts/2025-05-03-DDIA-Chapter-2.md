---
layout: post
title: DDIA - Chap02 - Data Models
published: true
---

The most important aspect of developing web-application is to determine the data model for it. A complext application might have multiple layers, however, ultimately it needs to access previously stored data. Hence it's one of the major decision to take to determine which data model to use.

### Relational Model:

The best known data model is based on SQL, which is based on relational model proposed by Edgar Codd, where the data is organized into tables, tables can have related through a set of attributes in the means of foreign key. The relational databases were mainly developed with business data transactions in mind, especially **transaction processing** and **batch processing**. 

Around the same time databases on top of network model and hierarchial model also became alternative to relational model, however the industry got dominated by the relational model.

In the network type of data model, a record could have multiple parents, and the link between records was not foreign keys, rather, they're more like pointers in a programming language.


### NoSQL:

NoSQL is the latest attempt of overthrow the dominance of the relational model. It's to be noted that NoSQL doesn't point to any specific technology, rather the name got sticky due to widespread requirement to *bypass the performance restriction relational model imposes, to scale the database easily*, even though it increases redundancy. 

One of the major issues with the relational model is **object-relational mismatch**. If the data is stored in multiple tables, then a translation layer is needed between the object structure in the application code and the database model, which is usually written in the application code itself. There are some framworks like ActiveRecord and Hibernate, categorized as **Object-relational mapping (ORM)**, which attempted to reduce the complexity by reducing the boilerplate code for this translation, however it still can't completely hide the complexity.

This is why self-container document like *JSON* representation become quite famous, and **Document-oriented databases** like MongoDB, CouchDB started supporting this type of data model.

Using and ID is always preferable whenever in doubt. As ID has no specific meaning to human, it never needs to change. The value that the ID refers, can be changed without any major impact.


### Which data model to choose?

##### One-to-many relationship:
Document model captures one-to-many relationship in optimized way. However, due to poor support of join in document databases, it would be preferable to use relational data model if the application needs many-to-many relationship. Graph models are natural to this use-case.

##### Schema flexibility:
Schema-on-read: The structure of the data is implicit, and only interpreted when the data is read
Schema-on-write: schema is explicit, and the database ensures the data written follows the schema

Schema changes are slow and require downtime. ALTER statement can take few milliseconds, except MySQL, where it can take minute and even hours, as it copies the entire table for ALTER statements. UPDATE statement can also take longer, as every row needs to be updated.

##### Record size:
It's recommended to keep the records small and avoid writing that increases the size of a record.


### Questions to ponder upon:
- Why do social networking sites not rely upon graph model databases, even though it would be a natural use case?
- Is there any performance benefit in using a default value for adding new columns with ALTER statements?
