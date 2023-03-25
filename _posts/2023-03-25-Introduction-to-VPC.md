---
published: false
---

In this blog post we're going to learn about VPC, a basic building block of creating a network infrastructure on the cloud environments. Even though we're going see some examples specific to AWS platform, this is supported by all the major cloud service providers, including the terminology and nomenclature, however, for sure, depending upon the cloud service providers, there are couple of restrictions imposed and conditions uplifted here and there. The basic understanding of VPC remains same across all the platforms.

VPC, Virutual Private Cloud, allows to deploy a logically isolated network infrastructure, on top of which different AWS resources can be deployed. It's to be noted that not all the services can be deployed on the VPC. As a rule of thumb, the services which are serverless in nature, i.e. deployment and scaling is automated by the cloud service provider, can not be deployed on the isolated network provided VPC. 

A VPC contains a IP address range, determined at the time of creation. For AWS platform, the VPC is bound to a particular region. The IP address range can not be modifed at later point of time, hence need to consider the future scope and requirements as well before deciding the IP range to be associated with.

Subnet is a logical split of the IP address range asscociated with the VPC. In case of AWS, one particular subnet belongs to a specific Availability Zone, and the all resources deployed under the subnet deployed to that particular AZ. Subnet IP address range within a VPC are not allowed to overlap.

Each VPC has got a router implicitly. The router isn't directly accessible, however the route table entries can be modified. The primary route table associated with the VPC has the main flag set. It is to be noted that each subnet can be associated with only a route table, however the same route table can be associated with the multiple subnets across different AZs. In case a particular subnet is not having route table explicitly assigned, the main route table implictly gets associated with it.

Internet gateway is a VPC component that allows the public internet connectivity from and to the VPC resources. The subnets for which route table redirects to the internet gateway are called public subnet, and the ones not having any route to the internet gateway are termed as private subnet. One VPC can be In case an EC2 instance has got a public IP but is placed under a private subnet, anybody from internet wouldn't be able to directly connect to this instance. It's to be noted that one Internet Gateway can be attached to only one VPC.

Similar to Internet Gateway, there's NAT gateway, which provides the outward connectivity to the public internet only from the private subnet. Here it's to be noted that the NAT instance itself is to be placed under a public subnet, and the route table entry of the private subnet is supposed to point to the NAT gateway. Also NAT gateway, being an managed instance, is deployed on a specific AZ, and hence to ensure high availability, it's recommeneded to deploy NAT gateway in the same AZ the private subnet is created. Besides, being a AWS managed instance, NAT gateways incurs hourly costs.




Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
