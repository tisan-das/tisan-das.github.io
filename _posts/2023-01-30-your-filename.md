---
published: false
---

#### Microservice Architecture
In this blog post we will learn about microservices. We would learn why microservices are evolved and preferred now-a-days over monolithic architecture. We would also learn about few patterns and useful ideas on microservices.

Microservice is an architectural approach to software development, where the overall software is broken down into multiple independent and loosely coupled services, communicating over a well-defined interface.Microservices are typically structured around the business needs, and are owned by a small team.

Earlier the software development used to follow the monolith architecture, where all the processes are run as single service. The codebase generally used to be maintained as single repo, and the application is used to deploy as a whole. However there's couple of disadvantages, which led to large adoption of microservice:
1. Scalability: As the whole application is deployed at a single go, scaling the application horizontally means certain portion of the application go unused, thus wasting resources
2. Coupling: Monolith architecture by nature becomes highly coupled. Even though there's disction between responsibiity of different modules or processes, however over a long time, these process becomes highly dependent on each-other, thus causing tight coupling.

The goal of microservice architecture is to make each team:
1. Autonomous: Implementation and operational decisions are independently taken
2. Specialized: Focused one solving one problem well
3. Built for business: Organized around business neeeds 

#### Monolith to microservices:
One starting point to convert a codebase from monolithic to microservice based is to consider the cohesivity. Club the functionalities that do related works and create a microservice out of that. Start small, with few modules and continue to separate them. Eventually it will result into architecture like following:




Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
