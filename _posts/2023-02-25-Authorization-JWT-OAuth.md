---
published: false
---
Authentication and authorization is one of the corner stones of designing services. As both the terms are used together, it gives the idea that both these terms are same. However it's far from the truth, conceptually they handle two different aspects of security. Authentication verifies the user identity, however authroization validates the access level. This blog post provides an introduction on the authorization portion, will discuss about OAuth, one of the most popular authorization mechanism available today.
<Add image for authorization vs authentication>

  
Before delving deep into OAuth, we would also discuss breifly about some other authentication mechanism as well:

#### HTTP Basic Auth:
HTTP Basic Auth is the most rudimentary type of authorization, where the client has to provide the credentials in the request itself. When the client sends the request wihtout any credential, the server responds with a 401 (Unauthorized) status code, and along side, it sends the following header:
```
WWW-Authenticate: <type> realm=<realm>
```
The WWW-Authenticate header denotes the type of authentication needs to be used, "Basic" in this case. The realm attribute value specifies the segment of resources, for which the credentials will be used. Not all the users would've the access permission for all set of resources, hence the endpoint expects credentials which have the access permission of the specified realm.
  
The credential is supposed to be provided in the request header section as following:

```
  Authorization: Basic Base64Encoding(userid:password)
```

Different servers has different mechanism for implementing HTTP Basic Auth. For NGINX web-server, need to create a htpasswd file with the credentials, and then specifying it with the aauth_basic directives, by specifying the realm.
```
  location /api {
    auth_basic           "Administrator’s Area";
    auth_basic_user_file /etc/apache2/.htpasswd; 
  }
```
  
  
### References:
  1. https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
  2. https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/
  3. https://www.ibm.com/docs/en/cics-ts/5.4?topic=concepts-http-basic-authentication
  4. https://www.twilio.com/docs/glossary/what-is-basic-authentication