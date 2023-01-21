---
published: false
---
## A New Post

This blogpost is written to jolt down several concepts of Docker, which are generally not needed for day-to-day activities for majority of the tasks, however these concepts provides an overview on the working principles of Docker.

#### Concept 01: Docker Image is built with layers
Dockerfile provides a template, a set of instructions, to create an image. Each instruction that changes the file-system, the resultant file-system with the change is stored as a layer. It's to be noted that only RUN, ADD, COPY instructions are the one which makes changes to the file-system. The instructions that are not updating the filesystem are stored as metadata and are generally can be inspected as part of config portion of the image.

-- Snippets to be inserted here

Note: Intermediate steps for the 
  
#### Concept 02: Docker images are built using containers

--- Snippets and explanantion 



Enter text in [Markdown](http://daringfireball.net/projects/markdown/). Use the toolbar above, or click the **?** button for formatting help.
