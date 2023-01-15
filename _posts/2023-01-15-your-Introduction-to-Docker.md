---
published: true
---

Docker provides an platform to build and deploy application on an isolated environment. The main technology behind the docker is containerization, which dictates that all the containers are self-sufficient run-time of the application, having it's own filesystem, network stack. The post here covers the fundamentals of docker, the goal here is to understand the basics, to have some experience with the docker client to create, run, inspect containers.


#### Comparision with Virtualization:
Virtualization is also a competitive technology compared to containers. However virutlization provides an abstraction on hardware level, it slices the resources like compute, memory, file-system, and then install a guest OS with the slices resources. Hence each VM has got it's own boot process. 

On the other hand container usees OS provided features to isolate the run-times on the process level, making it much more light-weight to run a container. More on this would be explored as part of another blog post in near future.

[Image for comparision]


[Docker Portion]

#### Docker clinet:

Docker CLI is having a specific set of commands called management commands. Each such command referes to specific resource that the docker daemon manages.
[Docker CLI Image]

Note: Majority of the docker client commands are legacy, just there for backward compatibility, and generally discouraged for new learners. These commands can be hidden by using environemnt variable:
```sh
export DOCKER_HIDE_LEGACY_COMMANDS=true
```

#### Docker Images:
Docker images are packages that contains all the dependencies along with the application itself. It works as template to containers. Docker images are stored on the repository. The images can be pushed with the push command or can be pulled from the repostiroty using pull command. It's be noted that inorder to push the image, the image is needed to be tagged properly first. Docker repositories are more populary called as registry. There are couple of docker registries available, including the public ones supported by Docker Inc like Docker Hub, Docker Store etc, also there're some third-party Docker registry providers as well, like [quay.io].

Following section provides a small example of creating a docker image from template:

```Dockerfile
FROM debian:buster-slim

ARG NGINX_PKG_TYPE=full
ENV NGINX_PKG=nginx-${NGINX_PKG_TYPE:-full}

RUN apt-get update \
      && apt-get install -y $NGINX_PKG \
      && rm -rf /var/lib/apt/lists/* \
      && rm /var/log/nginx/access.log \
      && rm /var/log/nginx/error.log \
      && ln -s /dev/stdout /var/log/nginx/access.log \
      && ln -s /dev/stderr /var/log/nginx/error.log

COPY ./html/ /var/www/html/

CMD ["/usr/sbin/nginx", "-g", "daemon off;"]

EXPOSE 80

STOPSIGNAL SIGQUIT
```
Note: ADD is an interesting docker template instruction, which is having more functionality compared to copy, it can be used to fetch remote files, to extract compressed files automatically. More on the docker template instructions can be found here at https://docs.docker.com/engine/reference/builder/

Note: Docker provides supports for ignoring files and directories to be included as part of docker image creation through .dockerignore file

```sh
docker image build -t tisan/nginx:latest .
```

Some useful commands to manage container images:
```sh
docker image ls
docker image prune
docker image pull [OPTIONS] NAME[:TAG|@DIGEST]
docker image push [OPTIONS] NAME[:TAG]
docker image rm [OPTIONS] IMAGE [IMAGE...]
docker image tag SOURCE_IMAGE[:TAG] TARGET_IMAGE[:TAG]
```


#### Container:

#### Persistence Storage:
Even though docker containers are preferred to be stateless, however there's certain scenarios, where a container might need to access some external data stored on disk drive, or else might need to store some persisting data. Docker provides support for these scenarios as well.

##### Bind mounts:
##### Volumes:


More on the Docker volumes can be found at https://docs.docker.com/storage/volumes/

#### Network:

Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
