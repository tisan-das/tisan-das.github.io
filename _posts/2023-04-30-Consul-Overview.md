---
published: false
---
With the advent of microservices, the networking got more complicated. Earlier, with the monolithic approach, the vertical scalability was pretty much simplistic in nature. The applications were viewed as 3-tier application, and majority of the traffic flow was north-south, i.e. majority of the data flow consisted of client request and response, may be in form of browser requests, or may be in form of API requests. Event the networking configuration was also simipler due to the nature of these 3 tiers, where the network flow was allowed from the downstream layer to the immediately upstream layer, and there a loadbalancer is usally placed, which works as reverse proxy server to the external users.

However with the advent of microservices, the 

Recently have came across consul, a service mesh solution provided by Hashicorp


#### References:
1. https://docs.aws.amazon.com/whitepapers/latest/serverless-multi-tier-architectures-api-gateway-lambda/three-tier-architecture-overview.html



