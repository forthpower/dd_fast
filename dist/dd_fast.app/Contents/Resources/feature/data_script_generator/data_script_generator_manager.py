#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据脚本生成器管理器
负责与主界面的对接，启动Flask服务器
"""

import threading
import webbrowser
import subprocess
import sys
import os
from pathlib import Path


class DataScriptGeneratorManager:
    """数据脚本生成器管理器"""
    
    def __init__(self):
        self.server_process = None
        self.port = 5011
        self.script_dir = Path(__file__).parent
    
    def get_button_config(self):
        """获取按钮配置"""
        return {
            "text": "📝 数据脚本生成器",
            "font": ("Arial", 20, "bold"),
            "bg": "#E74C3C",
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
        return "#E74C3C", "#C0392B"
    
    def open_feature(self):
        """打开数据脚本生成器"""
        try:
            # 检查必要文件是否存在
            if not self._check_files():
                print("错误: 数据脚本生成器文件不完整，请检查文件是否存在")
                return
            
            # 检查依赖是否安装
            if not self._check_dependencies():
                print("错误: 缺少必要的Python依赖，请先安装requirements.txt中的依赖")
                return
            
            # 启动Flask服务器
            self._start_server()
            
            # 打开浏览器
            self._open_browser()
            
            print(f"数据脚本生成器已启动！访问地址: http://localhost:{self.port}")
            
        except Exception as e:
            print(f"启动数据脚本生成器时出错: {str(e)}")
    
    def _check_files(self):
        """检查必要文件是否存在"""
        required_files = [
            "static/index.html",
            "backend/database/db_config.py",
            "backend/generator/script_generator.py",
            "backend/api/script_api.py"
        ]
        
        for file in required_files:
            if not (self.script_dir / file).exists():
                print(f"缺少文件: {file}")
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
            
            # 切换到数据脚本生成器目录
            os.chdir(self.script_dir)
            
            # 在后台线程中启动Flask服务器
            def run_server():
                try:
                    # 确保在数据脚本生成器目录中
                    os.chdir(self.script_dir)
                    
                    # 添加当前目录到Python路径
                    import sys
                    sys.path.insert(0, str(self.script_dir))
                    
                    # 直接导入并启动Flask应用
                    from flask import Flask
                    from flask_cors import CORS
                    from backend.api.script_api import script_api
                    
                    # 创建Flask应用
                    app = Flask(__name__, 
                              static_folder='static',
                              static_url_path='/static')
                    CORS(app)
                    
                    # 注册蓝图
                    app.register_blueprint(script_api, url_prefix='/api')
                    
                    # 添加根路由
                    @app.route('/')
                    def index():
                        return app.send_static_file('index.html')
                    
                    # 启动服务器
                    print(f"🚀 数据脚本生成器服务器已启动在端口 {self.port}")
                    app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
                    
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
                print("数据脚本生成器服务器已关闭")
        except Exception as e:
            print(f"关闭服务器时出错: {e}")
