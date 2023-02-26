---
published: true
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

  
  
### OpenID Connect:
An extension of Oauth specification, it includes some small info about the users. The token associated with OpenID Connect is termed as ID token, which is provided in JWT format. It's to be noted that the ID token certain times can be stored on different storage media or sent throught the front channel, hence it's recommenended never to use any sensitive or protected data in the ID token. Also in case the ID token is stored on the client side, or in some untrusted location, need to validate the token locally, to ensure no data is changed. Also anytime the application accepts ID token except from authroization server, needs to validate it.
  
### Access Token Type:
- Reference token: These are the access tokens which doesn't store any meaningful infromation on themselves, rather they can be thought of a pointer to such data. Reference tokens are useful if the access token needs to store some sensitive data, and it's also very easy to revoke the access token, however the primary disadvantage lies in scaling up the OAuth server, as large store would be needed. Besides, the application has to invoke the OAuth server each time to validate the token, which added a network call, thus significantly increasing the latency.
- Structured token: Thesse are the self encrypted or self-encoded tokens, which stores some information. The content of the access token can be read easily, hence no senstive data should be part of this token. JWT token is one such implementation of structured token. The main benefit is that these tokens can be locally validated, even though OAuth server provides support for Token Introspection Endpoint. One of the major hiccup with these kind of tokens are to check for revoked access tokens, which would need a network call to check through the Token Introspecition Endpoint.
  
### Token Lifetime:
The general convention is to have a short access token lifetime, and a longer lifetime for the refresh token. This way even though the access token is expired, the application can request a new access token using the refresh token, and this way it's also verified that the requested user is still having proper permission on the resource. This lifetime values are generally determined with the help of policy, and policies can also be associated with certain device type. This way, in case a mobile device is used, the refresh token can have a longer lifetime, as a shorter refresh token would mean the user will be redirected to browser, which is quite a slow process for mobile applications, and would impact user experience.
  
Also, depending upoon the type of user also the lifetime can be changed:
- Admin User: Access token lifetime: 1hr, refresh token lifetime: 24hr => login once in a day
- Consuemer User: Access token lifetime: 24 hr, refresh token lifetime: unlimited => login only once
- Priviledge Scope: Access token lifetime: 4hr, refresh token lifetime: None => Require auth for sensitive operations

### Handling Revoked and Invalidated Access Token
There are several reasons for which an access token is needed to be revoked and invalidated. Operations like account deactivation, user revokes permission for application, or password is modified, token lifetime changed, these are the few of the examples for which the OAuth server needs to revoke the active token. It's the responsibility of the API to validate the access tokens. Even though the local validation provides speed and efficiency, however it still needs to use the Token Introspection Endpoint to validate the access token is not invalidated.
It's to be noted that the OAuth server provides a Revocation Endpoint, to revoke the access token from the application side as well.
  
<Image of API gateway > 
  
### Local Validation of JWT Access token:
1. Check the key ID and algorithm used from the header of the JWT payload, and validate that the signature is matching with the header and content.
2. Check the claims are intended for this particular application:
  	i. iss: Issuer OAuth Server
  	ii. aud: Audience, genrally client_id is provided
  	iii. iat ,exp: Issuance time and Expiration time, the current time should be in-between these two timestamps
  	iv. nounce: Check the nounce val with earlier request

### Scope:
OAuth specification doesn't specify any particular values for scope, however it's used to denote the access level to the protected resource. If no scope value is provided, then by default it's understood to have full access to the resource requested. The scope is the concept of permission, gouping and roles, and is dependent upon which kind of API the application intends to invoke. Eg:
  photos:read
  photos:write
  
It's reccomended to have atleast two different scope for read-only and read-write mode to be available. Also these scope details are shown at the user consent screen.
  
### Authorization Code Flow:
  
### Client Credentials Grant Flow:
It's mainly used for machine-to-machine communication, no user interaction is needed. Primary usecase lies in an application trying to fetch it's own resource.
Question: Why needed?

```curl
  POST https://api.authorization-server.com/token
  grant_type=client_credentials
  scope=contacts&
  client_id=<CLIENT_ID>&
  client_secret=<CLIENT_SECRET>&
```

```json
  {
  	access_token:
  	expires_in:
  	scope:
  }
```
It's to be noted that refresh token isn't issued for client credentials grant flow, as this is mainly used by service accounts, that is for programmatic access, where the application itself is the resource owner.

  
### References:
  1. https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication
  2. https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/
  3. https://www.ibm.com/docs/en/cics-ts/5.4?topic=concepts-http-basic-authentication
  4. https://www.twilio.com/docs/glossary/what-is-basic-authentication
  5. https://cloud.google.com/docs/authentication/api-keys
  6. https://auth0.com/intro-to-iam/what-is-oauth-2
  7. https://www.udemy.com/course/oauth-2-simplified/
