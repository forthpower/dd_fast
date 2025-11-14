#!/usr/bin/env python3
"""
开发模式启动脚本
自动处理进程管理和热重载
"""

import os
import sys
import subprocess
import signal
import time
import requests
from pathlib import Path

class DevServer:
    def __init__(self):
        self.process = None
        self.port = 5010
        
    def start(self):
        """启动开发服务器"""
        print("🚀 启动 Schema Generator 开发服务器...")
        
        # 检查端口是否被占用
        if self._is_port_in_use():
            print(f"⚠️  端口 {self.port} 被占用，尝试停止现有进程...")
            self.stop()
            time.sleep(2)
        
        # 启动新进程
        try:
            self.process = subprocess.Popen(
                [sys.executable, "app.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务器启动
            print("⏳ 等待服务器启动...")
            for i in range(10):
                if self._is_server_ready():
                    print(f"✅ 服务器启动成功! http://localhost:{self.port}")
                    return True
                time.sleep(1)
            
            print("❌ 服务器启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def stop(self):
        """停止服务器"""
        if self.process:
            print("🛑 停止服务器...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def restart(self):
        """重启服务器"""
        print("🔄 重启服务器...")
        self.stop()
        time.sleep(1)
        return self.start()
    
    def _is_port_in_use(self):
        """检查端口是否被占用"""
        try:
            response = requests.get(f"http://localhost:{self.port}/health", timeout=1)
            return response.status_code == 200
        except:
            return False
    
    def _is_server_ready(self):
        """检查服务器是否就绪"""
        return self._is_port_in_use()
    
    def run(self):
        """运行开发服务器"""
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if not self.start():
            return
        
        try:
            print("💡 开发服务器运行中...")
            print("💡 修改代码会自动重载")
            print("💡 按 Ctrl+C 停止服务器")
            
            # 保持运行
            while True:
                time.sleep(1)
                
                # 检查进程是否还在运行
                if self.process and self.process.poll() is not None:
                    print("⚠️  服务器进程意外退出")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            print("👋 开发服务器已停止")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.stop()
        sys.exit(0)

if __name__ == "__main__":
    server = DevServer()
    server.run()
