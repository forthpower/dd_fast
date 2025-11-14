#!/bin/bash

# 杀死现有的Python进程
echo "🔄 停止现有服务器..."
pkill -f "python3 app.py" 2>/dev/null || true

# 等待端口释放
sleep 2

# 启动新服务器
echo "🚀 启动Schema Generator服务器..."
python3 app.py
