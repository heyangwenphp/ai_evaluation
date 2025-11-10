map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
        listen 80;
        server_name eva.kekepu.com;
        root /www/python/kekepu;

        add_header X-Accel-Buffering "no";
        add_header Cache-Control "no-cache";
        #add_header Connection "keep-alive";
        proxy_buffering off;
        proxy_hide_header Upgrade;

         location / {
            index  index.html index.htm ;
            try_files $uri $uri/ @router;
        }
        location @router {
                rewrite ^.*$ /index.html last;
        }
        location ^~ /Api/ {
            proxy_pass http://172.17.0.1:7001/Api/;
            proxy_http_version 1.1;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            #proxy_set_header Upgrade $http_upgrade;
            #proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 300;
            proxy_send_timeout 300;
            proxy_connect_timeout 300;
        }
        location ^~ /Index/ {
            proxy_pass http://172.17.0.1:7002/Index/;
            proxy_http_version 1.1;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            #proxy_set_header Upgrade $http_upgrade;
            #proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 300;
            proxy_send_timeout 300;
            proxy_connect_timeout 300;
        }

        location = /demo {
            return 301 $scheme://$host/demo/;
         }




        location ^~ /demo/ {
            proxy_pass http://172.17.0.1:7003/;
            proxy_http_version 1.1;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
            #proxy_set_header Upgrade $http_upgrade;
            #proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 900s;
            proxy_send_timeout 900s;
            proxy_connect_timeout 900s;
	        send_timeout 900s;
        }



        location ^~ /media/ {
            	#允许跨域请求的域，* 代表所有
        	add_header 'Access-Control-Allow-Origin' *;
        	#允许带上cookie请求
        	add_header 'Access-Control-Allow-Credentials' 'true';
        	#允许请求的方法，比如 GET/POST/PUT/DELETE
        	add_header 'Access-Control-Allow-Methods' *;
            #允许请求的header
        	add_header 'Access-Control-Allow-Headers' *;
        	alias  /www/python/media/;
       }

}
