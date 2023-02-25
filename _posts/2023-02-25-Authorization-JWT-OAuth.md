---
published: false
---
Authentication and authorization is one of the corner stones of designing services. As both the terms are used together, it gives the idea that both these terms are same. However it's far from the truth, conceptually they handle two different aspects of security. Authentication verifies the user identity, however authroization validates the access level. This blog post provides an introduction on the authorization portion, will discuss about OAuth, one of the most popular authorization mechanism available today.
<Add image for authorization vs authentication>

  
Before delving deep into OAuth, we would also discuss breifly about some other authentication mechanism as well:

## HTTP Basic Auth:
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
<HTTP Basic Auth Image>

It's to be noted that as credentials are transferred over a network call in this case, a secure layer like HTTPS is needed to ensure the credentials is safe from evasdropping or man-in-the-middle attack.

## API Keys:
API keys are another commonly used authentication mechanism, where the end-user has to create an API key beforehand by registering, and then including the API_KEY as part of the request. It's to be noted that even though HTTPS encrypts both query parameters and headers, before transmitting over network, it's advised to use the API Key in the header section, as majority of the web-server logs the request with the query parameters, and hence compromising logs of the web-server may leak the API key as well.
  
```curl
   curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "X-goog-api-key: API_KEY" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d @request.json \
    "https://translation.googleapis.com/language/translate/v2"
```
  
## OAuth:
OAuth is one of the mot used authorization mechanism. It's a authroization mechanism, in a sense that it's targeted to validate the access permission, rather than identifying user or validating credentials. OAuth specifies the use of an access token to verify the access permission. The RFC doesn't specifies any specific format for the OAuth, even though JWT is the most used format. The access tokens are not meant to be understand by the client requesting for a protected resource. It's only meant to be understood by the resource server and the OAuth server. However before going deep, we've to understand different actors or roles as mentioned by OAuth to understand the authorization flow better.
  
  
### OAuth Roles:
- Resource Owner: The user or the system that owns the protected resource
- User-Agent: The device which is used to access the protected reource
- OAuth Client: The application, that is requesting access to the protected resource
- Resource Server: The API or the server that is hosting the protected resource. It accepts and validates the access token. 
- Authorization Server: The OAuth server that validates the user credentials, and issues the access tokens. The OAuth server also has the facility of revoking the access tokens.

### OAuth Client Types:
 - Public Client: The applications that can't hold any secrets or credentials, like mobile app, single page app. Basically the applications which resides on user controlled devices. The main reason these kind of applications can't hold any secret or credentials, as they can be easily debugged or reverse engineered. 
 - Confidential Client: These are the application that can hold secrets or credentials. Basically all the server side applications belong to this category, as the executables are not directly accessible by the end-users, and can't be easily debugged.

### Communication Channels:
- Front Channel: The data is passed through user's address bar
- Back Channel: Server directly send the requests over a secured network call
  
### Registering the Client:
The first stage is of using OAuth is to register the client, ie the application, which needs the access to the protected resource. During the registration, depending upon the type of application, client ID and client secret is assigned. A list of redirect URIs are also provided, they're the same pages where the user will be redirected once authentication is successful. This also provides an additional security layer on the OAuth, where even though a rouge service can redirect to the authorization server, however they won't be abld to redirect the targeted user to their own site. It's advised not to provide any wildcard or any way for partial matching, which may help malicous attacker. It's to be noted that the generated client ID and client secret is needed to be treated as username and password, and hence the client secret should only be used with confidential clients, which can't be easily debugged or reversed-engineered.



  

  
### References:
  1. https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
  2. https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/
  3. https://www.ibm.com/docs/en/cics-ts/5.4?topic=concepts-http-basic-authentication
  4. https://www.twilio.com/docs/glossary/what-is-basic-authentication
  5. https://cloud.google.com/docs/authentication/api-keys
  6. https://auth0.com/intro-to-iam/what-is-oauth-2
