map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}
server {
        listen 80;
        server_name yuance.zeelin.cn;
        rewrite ^(.*)$ https://$host$1 permanent;
}
server {
        listen 443 ssl;
        server_name yuance.zeelin.cn;

        root /www/yuance;
	    access_log /var/log/nginx/yuance-access.log main;
        error_log /var/log/nginx/yuance-error.log warn;

        ssl_certificate /cert/zeelin.cn.pem;
        ssl_certificate_key /cert/zeelin.cn.key;
        ssl_session_cache           shared:SSL:1m;
        ssl_session_timeout 5m;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE:ECDH:AES:HIGH:!NULL:!aNULL:!MD5:!ADH:!RC4;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
        ssl_prefer_server_ciphers on;

        add_header X-Accel-Buffering "no";
        add_header Cache-Control "no-cache";
        #add_header Connection "keep-alive";
        proxy_buffering off;
        proxy_cache off;
        proxy_hide_header Upgrade;
       location / {
            index  index.html index.htm ;
            try_files $uri $uri/ @router;
        }
        location @router {
                rewrite ^.*$ /index.html last;
        }
        location = /brand {
            return 301 $scheme://$host/brand/;
        }

        location = /llm {
            return 301 $scheme://$host/llm/;
        }

        location ^~ /Api/ {
            proxy_pass http://172.17.0.1:9101/Api/;
            proxy_http_version 1.1;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
            #proxy_set_header Upgrade $http_upgrade;
            #proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 300;
            proxy_send_timeout 300;
            proxy_connect_timeout 300;
        }
        location ^~ /Index/ {
            proxy_pass http://172.17.0.1:9102/Index/;
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

        location ^~ /brand/ {
            proxy_pass http://172.17.0.1:9104/;
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
        location ^~ /api/ {
            proxy_pass http://172.17.0.1:9104/api/;
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
        location ^~ /llm/ {
            proxy_pass http://172.17.0.1:9200/;
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
        location ^~ /css/ {
            	#允许跨域请求的域，* 代表所有
        	add_header 'Access-Control-Allow-Origin' *;
        	#允许带上cookie请求
        	add_header 'Access-Control-Allow-Credentials' 'true';
        	#允许请求的方法，比如 GET/POST/PUT/DELETE
        	add_header 'Access-Control-Allow-Methods' *;
            #允许请求的header
        	add_header 'Access-Control-Allow-Headers' *;
        	alias  /python/ai_brand/public/css/;
        }
        location ^~ /js/ {
            	#允许跨域请求的域，* 代表所有
        	add_header 'Access-Control-Allow-Origin' *;
        	#允许带上cookie请求
        	add_header 'Access-Control-Allow-Credentials' 'true';
        	#允许请求的方法，比如 GET/POST/PUT/DELETE
        	add_header 'Access-Control-Allow-Methods' *;
            #允许请求的header
        	add_header 'Access-Control-Allow-Headers' *;
        	alias  /python/ai_brand/public/js/;
        }

         location ^~ /static/ {
            	#允许跨域请求的域，* 代表所有
        	add_header 'Access-Control-Allow-Origin' *;
        	#允许带上cookie请求
        	add_header 'Access-Control-Allow-Credentials' 'true';
        	#允许请求的方法，比如 GET/POST/PUT/DELETE
        	add_header 'Access-Control-Allow-Methods' *;
            #允许请求的header
        	add_header 'Access-Control-Allow-Headers' *;
        	alias  /python/LLMRisksEvaluation/app/static/;
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
        	alias  /python/ai_eva/media/;
       }
}
