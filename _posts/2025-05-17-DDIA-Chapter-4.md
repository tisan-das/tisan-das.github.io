---
layout: post
title: DDIA - Chap04 - Enconding and Evolution
published: true
---

All applications change, as do their requirements. With such changes, it's highly likely that the underlying data models also change. In this blog post, we will mainly discuss this.

With the advent of microservices, the changes are generally deployed with canary deployment, i.e., gradually. Due to this,  the following two types of compatibility need to be considered while changing the underlying data model:
1. **Backward compatibility**: The new code can read the data written by the older code
2. **Forward compatibility**: The older code can read the data written by the newer code. The older code needs to ignore the additions made by the newer code

While sending the data to other services across a network, or while storing the data, the program specific object needs to be encoded into a byte stream. This process of converting an in-memory object into a sequence of bytes is called encoding or serialization, and the reverse is called decoding or deserialization. Sometimes the are also called marshalling and unmarshalling, as the term serialization can sometimes cause a confustion. 

Different programming languages provide built-in support to marshal and unmarshal data. However, it's to be noted that they often neglect the portability of the marshalled data across different programming languages, and also often neglect the support of versioning. Due to these restrictions, it's always recommended not to rely upon language provided with built-in encoding support.

JSON, XML, and Binary variants of encoding are the most popular ones with microservices. They've their flaws, like categorizing a numerical value as an integer or float, however, their difficulty is often trumped by the difficulty it takes for different teams to agree on a common payload for inter-service communication.



### Thrift and Protocol Buffers:
Apache Thrift and Protocol Buffers are binary encoding libraries that require a schema for any data that needs encoding. Both the protocol requires the schema require the following:
- attribute name
- attribute type
- optional/required
- tag number of the attribute

```json
struct Person {
    1: required string userName,
    2: optional i64 favoriteNumber,
    3: optional list<string> interests
}


message Person {
    required string user_name = 1;
    optional int64 favorite_number = 2;
    repeated string interests = 3;
}
```

The names of the attributes can be changed independently, as the encoded data refers to the attributes through the tag number. Forward compatibility is achieved through this. Backward compatibility is achieved by adding new fields and marking them as optional. Also, only the optional fields can be deleted, and the same tag number should never be used in the future.

The primary reason thrift and protobuf protocols are selected over encoding formats like JSON and XML is primarily due to speed in serializing and deserializing large amounts of data.



### Avro:

Apache Avro is another binary encoding format, which is used in the context of big-data applications, and provides more flexibility in terms of schema evolution. The writer and reader schema don't have to be the same, they just need to be compatible.

```json
record Person {
    string userName;
    union { null, long } favoriteNumber = null;
    array<string> interests;
}
```


### To be explored:
1. Do the thrift, protocol buffer, and Avro encoding format supports nested structure?
2. Code example of using these binary encoding formats.
