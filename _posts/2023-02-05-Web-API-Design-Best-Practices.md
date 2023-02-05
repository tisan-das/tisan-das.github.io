---
published: false
---
In this blog post, we are going learn about the RESTful API design, a principle widely adopted by microservices to design interface so much that it became the de-facto standard. Here we will learn basics about REST, standard practices and how to utilize REST to create an intituive interface that clients can comsume in a meaningful way.

Basically, a well-designed Web-API should aim to support the following:
1. Platform independence: It wouldn't force clients consumign the APIs to be implemneted using a specific platform. The server and client can agree on using a specific protocol, and the format of 
2. Service evolution: APIs should be evolved and modify the implemnetation without impacting the existing functionality of the APIs

It's to be noted that the Representational State Transfer (REST) doesn't dictates use of specific protocol or media types' it's independet of these. However due to wide adoption of REST in microservices, and due to need of majority of the webservices to provide support thorugh web endpoints, the use of HTTP as underlying communication protocol became de-facto standard of REST.

The primary principles behind REST are as follows:
1. All the operations perfomed on resource (also called entity). The APIs are designed around the resources
2. Each resource has an URI, that uniquely indentifies the resource:
``` https://adventure-works.com/orders/1 ```
3. Clients interact by exchaing representation of resource:
```json {"orderId":1,"orderValue":99.90,"productId":1,"quantity":1} ```
4. REST APIs are stateless in nature. Server is expected to handle any incoming request in any order. The client isn't expected to store any information.

### Organize API Design around resources:



### References:
https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design

Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
