#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow可视化管理器
负责与主界面的对接，启动Flask服务器
"""

import threading
import webbrowser
import os
from pathlib import Path


class WorkflowVisualizerManager:
    """Workflow可视化管理器"""
    
    def __init__(self):
        self.server_process = None
        self.port = 5012
        self.script_dir = Path(__file__).parent
    
    def get_button_config(self):
        """获取按钮配置"""
        return {
            "text": "🔀 Workflow可视化",
            "font": ("Arial", 20, "bold"),
            "bg": "#9b59b6",
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
        return "#9b59b6", "#8e44ad"
    
    def open_feature(self):
        """打开Workflow可视化功能"""
        try:
            # 检查必要文件是否存在
            if not self._check_files():
                print("错误: Workflow可视化文件不完整，请检查文件是否存在")
                return
            
            # 检查依赖是否安装
            if not self._check_dependencies():
                print("错误: 缺少必要的Python依赖，请先安装requirements.txt中的依赖")
                return
            
            # 启动Flask服务器
            self._start_server()
            
            # 打开浏览器
            self._open_browser()
            
            print(f"Workflow可视化已启动！访问地址: http://localhost:{self.port}")
            
        except Exception as e:
            print(f"启动Workflow可视化时出错: {str(e)}")
    
    def _check_files(self):
        """检查必要文件是否存在"""
        required_files = [
            "static/index.html",
            "workflow_parser.py",
            "backend/api/workflow_api.py"
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
            
            # 切换到workflow目录
            os.chdir(self.script_dir)
            
            # 在后台线程中启动Flask服务器
            def run_server():
                try:
                    # 确保在workflow目录中
                    os.chdir(self.script_dir)
                    
                    # 添加当前目录到Python路径
                    import sys
                    sys.path.insert(0, str(self.script_dir))
                    
                    # 直接导入并启动Flask应用
                    from flask import Flask
                    from flask_cors import CORS
                    from feature.feishu.backend.api.workflow_api import workflow_api
                    
                    # 创建Flask应用
                    app = Flask(__name__, 
                              static_folder='static',
                              static_url_path='/static')
                    CORS(app)
                    
                    # 注册蓝图
                    app.register_blueprint(workflow_api, url_prefix='/api')
                    
                    # 添加根路由
                    @app.route('/')
                    def index():
                        return app.send_static_file('index.html')
                    
                    # 启动服务器
                    print(f"🚀 Workflow可视化服务器已启动在端口 {self.port}")
                    app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
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
                print("Workflow可视化服务器已关闭")
        except Exception as e:
            print(f"关闭服务器时出错: {e}")
