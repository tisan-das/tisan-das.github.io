---
published: true
---

NGINX is one of the most used web-server in the Internet. Besides being a web-server, NGINX can be used as proxy server, load-balancer, cache as well. In this blog we would explore on the such use-cases of NGINX. We would not only explore the theory behind these, we would also look from the configuration perspecitve as well.

### Basic NGINX commands:
```
nginx -s signal
```
The signal can be one of the following:
- stop: fast shutdown
- quit: graceful shutdown
- reload: reloading the configuration file

NGINX configuration file can be checked with the command:
```
nginx -t
```


### NGINX Configuration Basics

NGINX configuration file consists of directives. There's two types of directives- line directives are terminated by semi-colon, and block directives are terminated by the closing parenthesis. 

Directive examples:
- user: specifies the user and group used by the worker process, which accepts incoming requests
- worker_processes: defines the no. of worker processes, "auto" option sets the worker process count based on the number of cores available to the CPU
- worker_connections: the total number of connections can be concurrently served by each worker process. It's to be noted that total number of connection across all the worker processes can't exceed the maximum number of open files, which can be modified by worker_rlimit_nofile
- server: contains configuration of a virtual server. Each server can be identified with the server name and the port it's listening to. There can be multiple server listening to the same port, each differentiated by the server name i.e. host it's supposed to serve to. Also in case multiple server listening to the same port, one of them port will be assigned as default server. 

```conf
server {
    listen      192.168.1.1:80;
    server_name example.org www.example.org;
    ...
}

server {
    listen      192.168.1.1:80 default_server;
    server_name example.net www.example.net;
    ...
}

server {
    listen      192.168.1.2:80 default_server;
    server_name example.com www.example.com;
    ...
}
```

Following configuration prevents requests with no server name specified from further processing:
```conf
server {
    listen      80;
    server_name "";
    return      444;
}
```

There are couple of generic guidance with NGINX configuration:
- Never to provide 777 permission level
- To have a default root specified under the server block
- To use conditional statements as less as possible


There's a nice document on how NGINX selects the server and location block[6]. This document contains detailed description along with some examples. However just to give some basic idea,NGINX first selects the server and then matches the location block to handle the incoming request. Selection criteria for both type of resource following similar principle:
- Look for exact match (server: IP adrees filter first, then based on server name)
- In case an exact match doesn't exists, look for longest prefix match (server: leading wildcard first, then training wildcard entries)
- If no match found, then evaluate the regular expressions in top-down fashion




```conf
user www-data;
worker_processes auto;

events{
    worker_connections 512;
}

http{

    # Associates content-type with known file-formats, the definition exists in fine mime.types
    include mime.types; 

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/access.log;

    # Create a upstream server 
    upstream backend_server{
        server 127.0.0.1:32768;
        server localhost:32769;
        server 127.0.0.1:32770;
    }

    server{
        listen 80;
        root /etc/nginx/www/; # try_files to use this root if root not declared within scope

        location /fruit {
            alias /etc/nginx/www; # alias is substitue of location directory
            try_files $uri /index.html; # try_file check the individual files at dir $root
        }

        location /www {
            root /etc/nginx;
            try_files $uri =405;
            #try_files $uri /index.html;
        }

        location /crop {
            return 307 /www;
        }

        rewrite ^/crops/(.*) /www/$1;

        location ~* \.(png|jpeg|jpg) {
            root /etc/nginx/images;
            try_files $uri /example.png =403;
        }

        location /server {
            proxy_pass http://backend_server/;
        }
    }
}
```
The directive "proxy_pass" redirects the request to a proxied server. For the prefix based location directive, only the normalized URI gets updated and the request parameters are retained, however for regex based location directive, we've to explicitly provide the arguments. A detailed description is provided at the document[11]. Besides this proxy_pass directive also helps in load-balancing with the help of a upstream server configuration, which contains a list of server to which the request can be redirected to. NGINX has an inbuilt load-balancing which checks for the server health, and redirects the request to one of the available servers. There's couple of load-balancing methods available with NGINX:
- Round robin
- Least Connections (least_conn)
- IP Hash (ip_hash)
- Generic Hash
- Random
- Least Time to respond



### References
1. http://nginx.org/en/docs/beginners_guide.html
2. http://nginx.org/en/docs/ngx_core_module.html
3. http://nginx.org/en/docs/http/request_processing.html
4. https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/
5. https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/
6. https://www.digitalocean.com/community/tutorials/understanding-nginx-server-and-location-block-selection-algorithms
7. https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/
8. https://docs.nginx.com/nginx/admin-guide/security-controls/securing-http-traffic-upstream/
9. https://www.nginx.com/blog/nginx-caching-guide/
10. http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass
11. https://stackoverflow.com/questions/8130692/how-can-query-string-parameters-be-forwarded-through-a-proxy-pass-with-nginx
