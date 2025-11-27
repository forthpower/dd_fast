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
            import rumps
            
            # 检查必要文件是否存在
            if not self._check_files():
                error_msg = "Workflow可视化文件不完整，请检查文件是否存在"
                print(f"错误: {error_msg}")
                rumps.alert("错误", error_msg)
                return
            
            # 检查依赖是否安装
            if not self._check_dependencies():
                error_msg = "缺少必要的Python依赖，请先安装requirements.txt中的依赖"
                print(f"错误: {error_msg}")
                rumps.alert("错误", error_msg)
                return
            
            # 检查服务器是否已经在运行（主应用可能已经启动了）
            if self._is_server_running():
                print(f"检测到服务器已在端口 {self.port} 运行，直接打开浏览器")
                self._open_browser()
                return
            
            # 启动Flask服务器
            self._start_server()
            
            # 打开浏览器
            self._open_browser()
            
            print(f"Workflow可视化已启动！访问地址: http://localhost:{self.port}")
            
        except Exception as e:
            import traceback
            error_msg = f"启动Workflow可视化时出错: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            try:
                import rumps
                rumps.alert("错误", error_msg)
            except:
                pass
    
    def _check_files(self):
        """检查必要文件是否存在"""
        # 检查静态文件
        static_file = self.script_dir / "static" / "index.html"
        if not static_file.exists():
            print(f"缺少文件: static/index.html")
            return False
        
        # 检查workflow_parser.py
        parser_file = self.script_dir / "workflow_parser.py"
        if not parser_file.exists():
            print(f"缺少文件: workflow_parser.py")
            return False
        
        # 检查workflow_api.py（在feishu目录下，通过导入检查）
        try:
            from feature.feishu.backend.api.workflow_api import workflow_api
        except ImportError as e:
            print(f"无法导入 workflow_api: {e}")
            # 尝试检查文件是否存在
            project_root = self.script_dir.parent.parent
            api_file = project_root / "feishu" / "backend" / "api" / "workflow_api.py"
            if not api_file.exists():
                print(f"缺少文件: feature/feishu/backend/api/workflow_api.py")
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
    
    def _is_server_running(self):
        """检查服务器是否已经在运行"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except Exception:
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
                    
                except OSError as e:
                    if "Address already in use" in str(e):
                        print(f"⚠️ 端口 {self.port} 已被占用，可能主应用已启动服务器")
                        print("   将直接使用已运行的服务器")
                    else:
                        import traceback
                        traceback.print_exc()
                        print(f"❌ 启动Flask服务器失败: {e}")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"❌ 启动Flask服务器失败: {e}")
                finally:
                    # 恢复原始工作目录
                    try:
                        os.chdir(original_cwd)
                    except:
                        pass
            
            # 在后台线程中运行服务器
            server_thread = threading.Thread(target=run_server, daemon=True, name="WorkflowVisualizerServer")
            server_thread.start()
            
            # 等待服务器启动
            import time
            time.sleep(2)
            
        except Exception as e:
            # 恢复原始工作目录
            try:
                os.chdir(original_cwd)
            except:
                pass
            raise Exception(f"启动Flask服务器失败: {str(e)}")
    
    def _open_browser(self):
        """打开浏览器"""
        try:
            # 等待服务器启动（如果服务器已经在运行，这个检查会很快）
            import time
            max_wait = 10  # 最多等待10秒
            wait_interval = 0.5
            waited = 0
            
            while waited < max_wait:
                if self._is_server_running():
                    break
                time.sleep(wait_interval)
                waited += wait_interval
            
            if not self._is_server_running():
                print(f"⚠️ 等待 {max_wait} 秒后服务器仍未启动，但将尝试打开浏览器")
            
            # 打开浏览器
            url = f"http://localhost:{self.port}"
            print(f"正在打开浏览器: {url}")
            webbrowser.open(url)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"打开浏览器失败: {e}")
            try:
                import rumps
                rumps.alert("错误", f"打开浏览器失败: {str(e)}\n\n请手动访问: http://localhost:{self.port}")
            except:
                pass
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
                print("Workflow可视化服务器已关闭")
        except Exception as e:
            print(f"关闭服务器时出错: {e}")
