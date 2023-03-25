---
published: false
---

In this blog post we're going to learn about VPC, a basic building block of creating a network infrastructure on the cloud environments. Even though we're going see some examples specific to AWS platform, this is supported by all the major cloud service providers, including the terminology and nomenclature, however, for sure, depending upon the cloud service providers, there are couple of restrictions imposed and conditions uplifted here and there. The basic understanding of VPC remains same across all the platforms.

VPC, Virutual Private Cloud, allows to deploy a logically isolated network infrastructure, on top of which different AWS resources can be deployed. It's to be noted that not all the services can be deployed on the VPC. As a rule of thumb, the services which are serverless in nature, i.e. deployment and scaling is automated by the cloud service provider, can not be deployed on the isolated network provided VPC. 

A VPC contains a IP address range, determined at the time of creation. For AWS platform, the VPC is bound to a particular region. The IP address range can not be modifed at later point of time, hence need to consider the future requirements as well before deciding the IP range to be associated with.

Subnet is another



Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
