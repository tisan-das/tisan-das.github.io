---
published: true
---
In this blog post, we are going learn about RESTful API design, a principle widely adopted by microservices to design interfaces so much that it became the de-facto standard. Here we will learn basics about REST, standard practices, and how to utilize REST to create an intuitive interface that clients can consume in a meaningful way.

A well-designed Web-API should aim to support the following:
    1. Platform independence: It wouldn't force clients consuming the APIs to be implemented using a specific platform. The server and client can agree on using a specific protocol, and the format of 
    2. Service evolution: APIs should be evolved and modified the implemnetation without impacting the existing functionality of the APIs

It's to be noted that the Representational State Transfer (REST) doesn't dictate the use of specific protocols or media types' it's independent of these. However due to the wide adoption of REST in microservices, and due to the need of the majority of the web services to provide support through web endpoints, the use of HTTP as an underlying communication protocol became a de-facto standard of REST.

The primary principles behind REST are as follows:
    1. All the operations performed on the resource (also called entity). The APIs are designed around the resources
    2. Each resource has a URI, that uniquely identifies the resource:
        ``` https://adventure-works.com/orders/1 ```
    3. Clients interact by exchanging representation of resources:
        ```json {"orderId":1,"orderValue":99.90,"productId":1,"quantity":1} ```
    4. REST APIs are stateless. The server is expected to handle any incoming request in any order. The client isn't expected to store any information.

### Organize API Design around resources:
The APIs are recommended to be focused on the resources. Resource URIs should be based on the noun (resource) and not the verb (operations on the resource)
```http
https://adventure-works.com/orders // Good

https://adventure-works.com/create-order // Avoid
```

Entities are often grouped into collections (orders, customers). A collection is a separate resource from the item within the collection and should have its own URI. For example, the following URI might represent the collection of orders:
```http
https://adventure-works.com/orders
```

Adopt a consistent naming convention in URIs. In general, it helps to use plural nouns for URIs that reference collections. It's a good practice to organize URIs for collections and items into a hierarchy. For example, /customers are the path to the customer's collection, and /customers/5 is the path to the customer with an ID equal to 5. This approach helps to keep the web API intuitive. Also, many web API frameworks can route requests based on parameterized URI paths, so you could define a route for the path /customers/{id}.

Avoid requiring resource URIs more complex than collection/item/collection.

### Define API operations in terms of HTTP methods
HTTP method naming provides meaning to the operations performed by the APIs. The following are the most used HTTP methods:

1. POST: Creates a new resource. Details of the resource are provided as part of the payload. It either creates a resource and returns the ID of the resource or submits a request to process the request and returns the tracking ID. 
HTTP Status Codes:
    i. 200 (OK): Request is accepted, however, a new resource is not created
    ii. 201 (Created): New resource is created, location header contains the URI of the resource
    iii. 204 (No Content): Request is accepted, no new resource is created, and no response body
    

2. GET: Retrieves the representation of the resource based on ID 
HTTP Status Codes:
    i. 200 (OK): Successful 
    ii. 404 (Not Found): Requested resource isn't found
    iii. 204 (No Content): Request is fulfilled, however without any response body
    
3. PUT: creates or replaces attributes of the resource. Details of the object are provided as part of the payload. The payload body contains the whole representation of the resource. In case the resource exists, only necessary attributes are updated, otherwise, a new object is created. Just like the POST method, it can also submit the request for further processing and return a tracking ID.
HTTP Status Codes:
    i. 201 (Created): New resource is created
    ii. 200 (OK): No new resource is created
    iii. 204 (No Content): Request is accepted, no new resource created, and no response body
    iv. 409 (Conflict): Updating the resource isn't possible, some issue

4. PATCH: Performs partial update over a resource. Details to be updated are provided as part of the payload. The payload body contains only a partial representation of the resource, the attributes only needed to be updated. Thus it provides some efficiency in terms of bandwidth usage over the PUT method.
HTTP Status Codes:
    i. 400 (Bad Request): Malformed request
    ii. 409 (Conflict): The patch document is valid, but changes can't be applied at the current state

5. DELETE: Deletes a resource based on the provided resource ID.
HTTP Status Codes:
    i. 204 (No Content): Deletion completed, no further response is sent
    ii. 404 (Not Found): Requested resource doesn't exist

![](../images/REST-intro/httpVerbs.png)



### Conform to HTTP semantics
1. Media-Types:
The client and server agree upon the representation of the resource through Media-Types, also known as MIME-types. For non-binary objects, the vast majority of the application relies on JSON and XML.

The Content-Type header is used to specify the representation of the resource, and is placed in both request and resource:
```
POST https://adventure-works.com/orders HTTP/1.1
Content-Type: application/json; charset=utf-8
Content-Length: 57

{"Id":1,"Name":"Gizmo","Category":"Widgets","Price":1.99}
```
Besides, a client can also provide a list of accepted MIME-types:
```
GET https://adventure-works.com/orders/2 HTTP/1.1
Accept: application/json
```

HTTP Status Code:
   i. 415 (Unsupported Media Type): Server doesn't support the requested Media-Type provided
   ii. 406 (Not Acceptable): The server can't match any of the accepted Meida-Type requested

### Asynchronous operations
Certain times POST, PUT, PATCH, and DELETE operations need somewhat longer time to process the request, and waiting for the whole process to be completed, can add unacceptable latency, or gateway timeout. In these scenarios, it's better to make the operation asynchronous. We will learn in-depth about an asynchronous operation in an upcoming post. However for time being, as a response we've to provide the status of the request, so that the client can monitor the status:
```
HTTP/1.1 202 Accepted
Location: /api/status/12345
```

### Filter and paginate data
GET requests over a collection can cause iteration through all the resources, and the response set becomes too huge to process, or too large to be sent as a response to a single request. In these scenarios, it's better to have certain ways to limit the response.  
```
/orders?limit=25&offset=50
```

### Support partial responses for large binary resources
Generally, HTTP requests are not suitable to fetch large objects. It's better to retrieve the large objects as chunks.

It's suggested to first implement a HEAD method to get the Media-Type of the resource:
```
HEAD https://adventure-works.com/products/10?fields=productImage HTTP/1.1
```
Response: The Content-Length header specifies the size of the resource in bytes, and the Accept-Ranges header indicates that the server supports a request for partial fetch.
```
HTTP/1.1 200 OK

Accept-Ranges: bytes
Content-Type: image/jpeg
Content-Length: 4580
```

The client uses this info to request for data in specific bytes range:
```
GET https://adventure-works.com/products/10?fields=productImage HTTP/1.1
Range: bytes=0-2499
```
Response: Contains the data in the specified bytes range. The headers also provide the info regarding the range of content sent, along with the overall resource size. The HTTP Status Code 206 suggests the response contains partial content
```
HTTP/1.1 206 Partial Content

Accept-Ranges: bytes
Content-Type: image/jpeg
Content-Length: 2500
Content-Range: bytes 0-2499/4580

[...]
```

### Versioning a RESTful web API
As the service evolves, it's accepted that the APIs would also evolve. However, from the client side, it would be difficult to keep track of all the changes and make changes on short notice. Adding a few new attributes in response might not cause the client code to fail, however, drastic changes, like a change in resource representation, or removal of some attributes can cause the client code to fail. It's always recommended to follow versioning when designing APIs to accommodate this kind of issue. 


### References:
1. [API Design Best Practices](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)

