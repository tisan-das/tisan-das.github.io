---
published: true
---

NGINX is one of the most used web-server on the Internet. Besides being a web server, NGINX can be used as a proxy server, load-balancer, and cache as well. In this blog, we would explore such use cases of NGINX. We would not only explore the theory behind these, but we would look from the configuration perspective as well.

### Basic NGINX commands:
```
nginx -s signal
```
The signal can be one of the following:
- stop: fast shutdown
- quit: graceful shutdown
- reload: reloading the configuration file

NGINX configuration file can be validated with the command:
```
nginx -t
```


### NGINX Configuration Basics

NGINX configuration file consists of directives. There are two types of directives- line directives are terminated by a semi-colon, and block directives are terminated by the closing parenthesis. 

#### Directives:
- user: specifies the user and group used by the worker process, which accepts incoming requests
- worker_processes: defines the no. of worker processes, "auto" option sets the worker process count based on the number of cores available to the CPU
- worker_connections: the maximum number of connections that can be served concurrently by each worker process. It's to be noted that the total number of connections across all the worker processes can't exceed the maximum number of open files, which can be modified by the directive "worker_rlimit_nofile"
- server: contains the configuration of a virtual server. Each server can be identified with the server name and the port it's listening to. There can be multiple servers listening to the same port, each differentiated by the server name i.e. host it's supposed to serve. Also in case, multiple servers listen to the same port, one of them would be assigned as the default server. Following is one such example configuration:
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

The following configuration prevents requests with no server name specified from further processing:
```conf
server {
    listen      80;
    server_name "";
    return      444;
}
```

#### Generic Guidelines
There is a couple of generic guidance with NGINX configuration:
- Never provide 777 permission level
- To have a default root specified under the server block
- To use conditional statements as less as possible


#### Server and location block selection:
There's a good article on how NGINX selects the server and location block[6]. This document contains a detailed description along with some examples. However just to give some basic idea, NGINX first selects the server and then matches the location block to handle the incoming request. Selection criteria for both types of resource follow a similar approach:
- Look for an exact match (server: IP address filter first, then based on server name)
- In case an exact match doesn't exist, look for the longest prefix match (server: leading wildcard first, then training wildcard entries)
- If no match is found, then evaluate the regular expressions in a top-down manner


#### NGINX sample configuration:
```conf
user www-data;
worker_processes auto;

events{
    worker_connections 512;
}

http{

    # Associates content type with known file formats, the definition exists in fine mime.types
    include mime.types; 

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/access.log;

    # Create an upstream server 
    upstream backend_server{
        server 127.0.0.1:32768;
        server localhost:32769;
        server 127.0.0.1:32770;
    }

    server{
        listen 80;
        root /etc/nginx/www/; # try_files to use this root if the root is not declared within the scope

        location /fruit {
            alias /etc/nginx/www; # alias is substitute of location directory
            try_files $uri /index.html; # try_file check the individual files at the dir $root
        }

        location /www {
            root /etc/nginx; # the location directory becomes $root/www
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

#### Load-balancing:
The directive "proxy_pass" redirects the request to a proxied server. For the prefix-based location directive, only the normalized URI gets updated and the request parameters are retained, however, for the regex-based location directive, we've to explicitly provide the arguments. A detailed description is provided in the document[11]. Besides, this proxy_pass directive also helps in load-balancing with the help of an upstream server configuration, which contains a list of servers, to which the request can be redirected to. The load-balancing mechanism also checks whether the servers are up individually and redirects the request to one of the available servers. There are a couple of types of load-balancing available with NGINX:
- Round robin
- Least Connections (least_conn)
- IP Hash (ip_hash)
- Generic Hash
- Random
- Least Time to respond


#### Cache
NGINX has also got in-built support for the cache. Following is one of the most simple examples:
```conf
proxy_cache_path /path/to/cache levels=1:2 keys_zone=my_cache:10m max_size=10g 
                 inactive=60m use_temp_path=off;

server {
    # ...
    location / {
        proxy_cache my_cache;
        proxy_pass http://my_upstream;
    }
}
```
The document as referred to by [11] provides a detailed description of different cache parameters supported by NGINX. Would request you to check the page as well to get a firm grasp on different cache configurations.


### References
1. [NGINX: Beginner’s Guide](http://nginx.org/en/docs/beginners_guide.html)
2. [NGINX: Core functionality](http://nginx.org/en/docs/ngx_core_module.html)
3. [How NGINX process requests](http://nginx.org/en/docs/http/request_processing.html)
4. [NGINX: Pitfalls and Common Mistakes](https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/)
5. [NGINX: If is evil](https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/)
6. [Understanding Nginx Server and Location Block Selection Algorithms](https://www.digitalocean.com/community/tutorials/understanding-nginx-server-and-location-block-selection-algorithms)
7. [NGINX: HTTP Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/)
8. [NGINX: Securing HTTP Traffic](https://docs.nginx.com/nginx/admin-guide/security-controls/securing-http-traffic-upstream/)
9. [A Guide to Caching with NGINX](https://www.nginx.com/blog/nginx-caching-guide/)
10. [NGINX module ngx_http_proxy_module](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)
11. [Forward query string parameters with proxy_pass directive in NGINX](https://stackoverflow.com/questions/8130692/how-can-query-string-parameters-be-forwarded-through-a-proxy-pass-with-nginx)
