#!/bin/sh
echo "停止服务开始"
kill -9 `ps -ef|grep ai_admin:app|awk '{print $2}'`
kill -9 `ps -ef|grep ai_index:app|awk '{print $2}'`
kill -9 `ps -ef|grep demo.py|awk '{print $2}'`
echo "停止服务结束"

echo "启动服务开始"
nohup gunicorn -w 2 -k uvicorn.workers.UvicornWorker ai_admin:app -b 0.0.0.0:7001  > logs/admin.log 2>&1 &
nohup gunicorn -w 5  -k uvicorn.workers.UvicornWorker ai_index:app -b 0.0.0.0:7002 --timeout 900 > logs/index.log 2>&1 &
nohup python3 demo.py > logs/demo.log 2>&1 &
echo "启动服务结束"
echo "启动成功"
