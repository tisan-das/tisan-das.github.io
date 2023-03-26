---
published: true
---

In this blog post we're going to learn about VPC, a basic building block of creating a network infrastructure on the cloud environments. Even though we're going see some examples specific to AWS platform, this is supported by all the major cloud service providers, including the terminology and nomenclature, however, for sure, depending upon the cloud service providers, there are couple of restrictions imposed and conditions uplifted here and there. The basic understanding of VPC remains same across all the platforms.

VPC, Virutual Private Cloud, allows to deploy a logically isolated network infrastructure, on top of which different AWS resources can be deployed. It's to be noted that not all the services can be deployed on the VPC. As a rule of thumb, the services which are serverless in nature, i.e. deployment and scaling is automated by the cloud service provider, can not be deployed on the isolated network provided VPC. 

A VPC contains a IP address range, determined at the time of creation. For AWS platform, the VPC is bound to a particular region. The IP address range can not be modifed at later point of time, hence need to consider the future scope and requirements as well before deciding the IP range to be associated with.
![](../images/vpc-intro/vpcSettings_dnsHostname.png)

Subnet is a logical split of the IP address range asscociated with the VPC. In case of AWS, one particular subnet belongs to a specific Availability Zone, and the all resources deployed under the subnet deployed to that particular AZ. Subnet IP address range within a VPC are not allowed to overlap.
![](../images/vpc-intro/subnetSettings.png)

Each VPC has got a router implicitly. The router isn't directly accessible, however the route table entries can be modified. The primary route table associated with the VPC has the main flag set. It is to be noted that each subnet can be associated with only a route table, however the same route table can be associated with the multiple subnets across different AZs. In case a particular subnet is not having route table explicitly assigned, the main route table implictly gets associated with it.
![](../images/vpc-intro/routeTable.png)

Internet gateway is a VPC component that allows the public internet connectivity from and to the VPC resources. The subnets for which route table redirects to the internet gateway are called public subnet, and the ones not having any route to the internet gateway are termed as private subnet. One VPC can be In case an EC2 instance has got a public IP but is placed under a private subnet, anybody from internet wouldn't be able to directly connect to this instance. It's to be noted that one Internet Gateway can be attached to only one VPC.
![](../images/vpc-intro/internetGateway.png)
![](../images/vpc-intro/igRouteEntry.png)


Similar to Internet Gateway, there's NAT gateway, which provides the outward connectivity to the public internet only from the private subnet. Here it's to be noted that the NAT instance itself is to be placed under a public subnet, and the route table entry of the private subnet is supposed to point to the NAT gateway. Also NAT gateway, being an managed instance, is deployed on a specific AZ, and hence to ensure high availability, it's recommeneded to deploy NAT gateway in the same AZ the private subnet is created. Besides, being a AWS managed instance, NAT gateways incurs hourly costs.


#### Traffic Privacy:
Security Group:
- Applied at the network interface level of the resources
- Spans across multiple AZ, multiple subnets
- Stateful nature: allows the return traffic automatically
- Supports allow rule only
- Multiple Security Groups can be applied to the same resource: the rules gets aggregrated
![](../images/vpc-intro/secGroup.png)

Network ACL:
- Applied on subnet level
- One subnet can only be associated with one NACL at a time
- Multiple subnets can use the same NACL
- Besides having allow rule, NACL supports deny rule as well unlike Security Group
- Stateless: need to explicitly allow the outgoing traffic for incoming ones
![](../images/vpc-intro/nacl.png)


VPC Peering:
VPC peering provides a networking capability to enable the resources across two VPC communicate with each other through private IP adresses. The VPC pair can be across different region, even across different AWS accounts. In case the VPC peering is configured for the VPC pair present in different AWS account, a peering request is pushed to the target AWS account, and is needed to be accepted within an acceptance time. 

![](../images/vpc-intro/peeringRouting.png)

It's to be noted that VPC peering doesn't support transitive routing. Hence in case need to interconnect multiple VPC, then a full mesh topology with VPC peering is needed to be established.

VPC Endpoint:
Enables to connect to supported AWS services through private connection. The traffic doesn't leave the Amazon network. We would also explore more on this later as part of a project.
![](../images/vpc-intro/endpoints.png)


Transit Gateway: 
Transit gateway is advertised as the cloud router in AWS. This follows the hub-and-spoke model, where the transit gateway servers as the central hub and manages network to different private networks. This is also one of the resource which costs per hour basis. We would learn different use cases of transit gateway in a different blog post.


### References:
1. [AWS VPC Beginner to Pro - Virtual Private Cloud Tutorial](https://www.youtube.com/watch?v=g2JOHLHh4rI)
2. [AWS VPC User Guide](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
3. [AWS VPC Peering](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html)
4. [AWS PrivateLink Concepts](https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html)
5. [AWS Transit Gateway](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html)
