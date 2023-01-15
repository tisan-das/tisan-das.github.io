---
published: true
---

Docker provides an platform to build and deploy application on an isolated environment. The main technology behind the docker is containerization, which dictates that all the containers are self-sufficient run-time of the application, having it's own filesystem, network stack. The post here covers the fundamentals of docker, the goal here is to understand the basics, to have some experience with the docker client to create, run, inspect containers.


#### Comparision with Virtualization:
Virtualization is also a competitive technology compared to containers. However virutlization provides an abstraction on hardware level, it slices the resources like compute, memory, file-system, and then install a guest OS with the slices resources. Hence each VM has got it's own boot process. 

On the other hand container usees OS provided features to isolate the run-times on the process level, making it much more light-weight to run a container. More on this would be explored as part of another blog post in near future.

[Image for comparision]

[Docker Portion]
Note: Majority of the docker client commands are legacy, just there for backward compatibility, and generally discouraged for new learners. These commands can be hidden by using environemnt variable:
```sh
export DOCKER_HIDE_LEGACY_COMMANDS=true
```

#### Container Images:
Image
  



Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
