#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow管理器
负责与主界面的对接，启动HTTP服务器
"""

import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser
import subprocess
import sys
import os
from pathlib import Path


class WorkflowManager:
    """Workflow管理器"""
    
    def __init__(self):
        self.server_process = None
        self.port = 8000
        self.workflow_dir = Path(__file__).parent
    
    def get_button_config(self):
        """获取按钮配置"""
        return {
            "text": "🌐 Primer Workflow 编辑器",
            "font": ("Arial", 20, "bold"),
            "bg": "#FF6B35",
            "fg": "black",
            "relief": "flat",
            "width": 25,
            "height": 3,
            "cursor": "hand2",
            "bd": 0,
            "highlightthickness": 0
        }
    
    def get_hover_colors(self):
        """获取悬停颜色"""
        return "#FF6B35", "#E55A2B"
    
    def open_feature(self):
        """打开Workflow编辑器"""
        try:
            print("🔍 检查Workflow编辑器文件...")
            
            # 检查必要文件是否存在
            if not self._check_files():
                error_msg = "Workflow编辑器文件不完整，请检查以下文件是否存在:\n"
                required_files = [
                    "workflow-explorer.html",
                    "workflow-explorer.js", 
                    "explorer-demo.html",
                    "start.py"
                ]
                for file in required_files:
                    exists = (self.workflow_dir / file).exists()
                    error_msg += f"- {file}: {'✅' if exists else '❌'}\n"
                
                print(f"❌ {error_msg}")
                messagebox.showerror("错误", error_msg)
                return
            
            print("✅ 文件检查通过")
            
            # 启动HTTP服务器
            print("🚀 启动HTTP服务器...")
            self._start_server()
            
            # 打开浏览器
            print("🌐 打开浏览器...")
            self._open_browser()
            
            print("✅ Workflow编辑器启动完成")

        except Exception as e:
            error_msg = f"启动Workflow编辑器时出错: {str(e)}"
            print(f"❌ {error_msg}")
            messagebox.showerror("错误", error_msg)
    
    def _check_files(self):
        """检查必要文件是否存在"""
        required_files = [
            "workflow-explorer.html",
            "workflow-explorer.js", 
            "explorer-demo.html",
            "start.py"
        ]
        
        for file in required_files:
            if not (self.workflow_dir / file).exists():
                return False
        return True
    
    def _start_server(self):
        """启动HTTP服务器"""
        try:
            # 使用Python的http.server模块启动服务器
            import http.server
            import socketserver
            
            # 创建自定义的HTTP请求处理器，指定工作目录
            workflow_dir_str = str(self.workflow_dir)
            class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=workflow_dir_str, **kwargs)
            
            # 在后台线程中启动服务器
            def run_server():
                try:
                    with socketserver.TCPServer(("", self.port), CustomHTTPRequestHandler) as httpd:
                        self.server_process = httpd
                        print(f"🚀 Workflow编辑器服务器已启动在端口 {self.port}")
                        print(f"📁 服务器根目录: {self.workflow_dir}")
                        httpd.serve_forever()
                except OSError as e:
                    if e.errno == 48:  # Address already in use
                        print(f"❌ 端口 {self.port} 已被占用，尝试使用端口 {self.port + 1}")
                        self.port += 1
                        self._start_server()
                    else:
                        print(f"❌ 启动服务器失败: {e}")
                except Exception as e:
                    print(f"❌ 服务器运行错误: {e}")
            
            # 在后台线程中运行服务器
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
        except Exception as e:
            raise Exception(f"启动HTTP服务器失败: {str(e)}")
    
    def _open_browser(self):
        """打开浏览器"""
        try:
            # 等待服务器启动
            import time
            time.sleep(2)  # 增加等待时间
            
            url = f"http://localhost:{self.port}/workflow-explorer.html"
            print(f"🌐 正在打开浏览器: {url}")
            
            # 打开浏览器
            webbrowser.open(url)
            print(f"✅ 浏览器已打开: {url}")
            
        except Exception as e:
            print(f"❌ 打开浏览器失败: {e}")
            # 提供手动访问的URL
            url = f"http://localhost:{self.port}/workflow-explorer.html"
            print(f"💡 请手动在浏览器中访问: {url}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.server_process:
                self.server_process.shutdown()
                self.server_process = None
                print("Workflow服务器已关闭")
        except Exception as e:
            print(f"关闭服务器时出错: {e}")
