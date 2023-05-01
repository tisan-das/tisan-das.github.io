---
published: false
---
With the advent of microservices, the networking got more complicated. Earlier, with the monolithic approach, the vertical scalability was pretty much simplistic in nature. The applications were viewed as 3-tier application, and majority of the traffic flow was north-south, i.e. majority of the data flow consisted of client request and response, may be in form of browser requests, or may be in form of API requests. Event the networking configuration was also simipler due to the nature of these 3 tiers, where the network flow was allowed from the downstream layer to the immediately upstream layer, and there a loadbalancer is usally placed, which works as reverse proxy server to the external users.
// Use of east-west service
// image

However with the advent of microservices, the complextiy in infrastructure is only increased. The first issue being, with microservices, the deployment can spread across multiple regions, and multiple instances of the service can be online or go down, which makes the networking harder. Also, the loadbalancing also becomes dynamic in nature. Thus it produces three distinct categories of problems which service mesh tries to netrualize:
1. Service Discovery: How to discover the services over the network to connect to
2. Configuration: How to update configuration of all instacens of a specific service at one go
3. Network Segmentation: How to simplify the firewall rules, and basically to abstract them to the service layer
All the above categories are related to service-to-service communication, and service mesh implments a low latency multi-platform networking solution for service-to-service communication. There's couple of enterprise level solutions offered by different service provides including Istio service mesh by Ishito, Consul by Hashicorp etc. Here, we would have some overview and hands-on on the Consul service mesh, however the theory behind the service mesh remains same, and applicable to the other service meshes as well.

Consul consists of two planes:
1. Control Plane:
	- controls data packet flow between the services
    - maintains service registry: keeps track of all the services along with their IP and health checks
    - services are registered with to the control plane
    - configuration specific to service is pushed to the key-value store, which in turn propagates the configufation to all the existing instances of the service
    - rules:
    - responsible of maintaining the service mesh
2. Data Plane: 
	- forwards the actual data packets
    - handles the communication between services
    
    
Consul control place consists of two types of agents- server agent and client client agent. The server agent creates a datacenter, which consists of a leader server agent, and rest of them are follower server agents. The server agents are the ones that stores all the service related info and does the heavey lifting of enforcing service discovery and access rules. It's generally advised to have 3 or 5 server agents, beyond which the overhead can negatively impact on the performance. However there's no such restriction on the client agents, large no of organizations follows datacenters with 5000 client agents, and couple of organization even maitains datacenter with tens of thousands of client agent.

The leader among the server agents is selected based upon a specific consesus algorithm. All the queries and the transactions are processed by the leader, the followers forwards the requests received from the client agents to the leader, and leader in-turn replicates all the updations to the followers.

// replication image

All the server and client agents participates in a LAN gossip pool. Agents in the pool propagate the health check information across the cluster. Agent gossip communication occurs on port 8301 using UDP. Agent gossip falls back to TCP if UDP is not available. 
// lan gossip image
 


#### References:
1. https://docs.aws.amazon.com/whitepapers/latest/serverless-multi-tier-architectures-api-gateway-lambda/three-tier-architecture-overview.html
2. https://istio.io/latest/about/service-mesh/
3. https://developer.hashicorp.com/consul/docs
4. https://developer.hashicorp.com/consul/docs/architecture

