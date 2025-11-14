#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema Generator管理器
负责与主界面的对接，启动Flask服务器
"""

import tkinter as tk
from tkinter import messagebox
import threading
import webbrowser
import subprocess
import sys
import os
from pathlib import Path


class SchemaGeneratorManager:
    """Schema Generator管理器"""
    
    def __init__(self):
        self.server_process = None
        self.port = 5010
        self.schema_dir = Path(__file__).parent
    
    def get_button_config(self):
        """获取按钮配置"""
        return {
            "text": "📊 Schema 生成器",
            "font": ("Arial", 20, "bold"),
            "bg": "#8E44AD",
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
        return "#8E44AD", "#7D3C98"
    
    def open_feature(self):
        """打开Schema生成器"""
        try:
            # 检查必要文件是否存在
            if not self._check_files():
                messagebox.showerror("错误", "Schema生成器文件不完整，请检查文件是否存在")
                return
            
            # 检查依赖是否安装
            if not self._check_dependencies():
                messagebox.showerror("错误", "缺少必要的Python依赖，请先安装requirements.txt中的依赖")
                return
            
            # 启动Flask服务器
            self._start_server()
            
            # 打开浏览器
            self._open_browser()
            
            messagebox.showinfo("成功", f"Schema生成器已启动！\n\n访问地址: http://localhost:{self.port}\n\n点击确定后会自动打开浏览器")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动Schema生成器时出错: {str(e)}")
    
    def _check_files(self):
        """检查必要文件是否存在"""
        required_files = [
            "app.py",
            "static/index.html",
            "static/script.js",
            "requirements.txt"
        ]
        
        for file in required_files:
            if not (self.schema_dir / file).exists():
                return False
        return True
    
    def _check_dependencies(self):
        """检查Python依赖是否安装"""
        try:
            import flask
            import flask_cors
            return True
        except ImportError:
            return False
    
    def _start_server(self):
        """启动Flask服务器"""
        try:
            # 保存当前工作目录
            original_cwd = os.getcwd()
            
            # 切换到schema_generator目录
            os.chdir(self.schema_dir)
            
            # 在后台线程中启动Flask服务器
            def run_server():
                try:
                    # 确保在schema_generator目录中
                    os.chdir(self.schema_dir)
                    
                    # 使用subprocess启动Flask应用
                    self.server_process = subprocess.Popen([
                        sys.executable, "app.py"
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(self.schema_dir))
                    
                    print(f"🚀 Schema生成器服务器已启动在端口 {self.port}")
                    
                    # 等待进程结束
                    self.server_process.wait()
                    
                except Exception as e:
                    print(f"❌ 启动Flask服务器失败: {e}")
                finally:
                    # 恢复原始工作目录
                    os.chdir(original_cwd)
            
            # 在后台线程中运行服务器
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # 等待服务器启动
            import time
            time.sleep(2)
            
        except Exception as e:
            # 恢复原始工作目录
            os.chdir(original_cwd)
            raise Exception(f"启动Flask服务器失败: {str(e)}")
    
    def _open_browser(self):
        """打开浏览器"""
        try:
            # 等待服务器启动
            import time
            time.sleep(3)
            
            # 打开浏览器
            webbrowser.open(f"http://localhost:{self.port}")
        except Exception as e:
            print(f"打开浏览器失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
                print("Schema生成器服务器已关闭")
        except Exception as e:
            print(f"关闭服务器时出错: {e}")
