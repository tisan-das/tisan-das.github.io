---
published: false
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


```conf
user www-data;
worker_processes auto;

events{
    worker_connections 512;
}

http{
    include mime.types;

    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/access.log;

    upstream backend_server{
        server 127.0.0.1:32768;
        server localhost:32769;
        server 127.0.0.1:32770;
    }

    server{
        listen 80;
        root /etc/nginx/www/; # try_files using this root if not defined

        location /fruit {
            alias /etc/nginx/www;
            try_files $uri /index.html;
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

### References
1. http://nginx.org/en/docs/beginners_guide.html
2. http://nginx.org/en/docs/ngx_core_module.htm
3. 









