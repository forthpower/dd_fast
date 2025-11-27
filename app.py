#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dd_fast - 使用rumps实现的系统托盘应用
"""

import rumps
import sys
import os
import threading

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 尝试从项目路径导入，如果失败则尝试打包路径
try:
    from feature.schema_generator.schema_generator_manager import SchemaGeneratorManager
except ImportError:
    try:
        from dist.dd_fast._internal.feature.schema_generator.schema_generator_manager import SchemaGeneratorManager
    except ImportError:
        # 如果都失败，尝试添加路径后导入
        import sys
        if hasattr(sys, '_MEIPASS'):  # PyInstaller打包环境
            sys.path.insert(0, os.path.join(sys._MEIPASS, 'feature'))
        from feature.schema_generator.schema_generator_manager import SchemaGeneratorManager

from feature.file_duplicator.file_duplicator_manager import FileDuplicatorManager
from feature.command_tool.command_tool_manager import CommandToolManager
from feature.data_script_generator.data_script_generator_manager import DataScriptGeneratorManager
from feature.workflow.workflow_visualizer_manager import WorkflowVisualizerManager


class DDFastApp(rumps.App):
    """dd_fast 系统托盘应用"""
    
    def __init__(self):
        super(DDFastApp, self).__init__("dd_fast")
        
        # 初始化功能管理器
        self.file_duplicator_manager = FileDuplicatorManager()
        self.schema_generator_manager = SchemaGeneratorManager()
        self.command_tool_manager = CommandToolManager()
        self.data_script_generator_manager = DataScriptGeneratorManager()
        self.workflow_visualizer_manager = WorkflowVisualizerManager()
        
        # 标记服务器是否已启动
        self._server_started = False
        
        # 设置菜单
        self.menu = [
            "文件复制器",
            "Schema生成器",
            "命令大全",
            "数据脚本生成器",
            "Workflow可视化",
            None
        ]
        
        # 延迟启动workflow Flask服务器（在应用运行后启动，避免阻塞主线程）
        # 使用rumps的定时器在1秒后启动服务器
        rumps.Timer(self._delayed_start_server, 1).start()
    
    def _delayed_start_server(self, _):
        """延迟启动服务器（在应用运行后调用，避免阻塞主线程）"""
        if not self._server_started:
            self._server_started = True
            self._start_workflow_server()
    
    def _start_workflow_server(self):
        """启动workflow Flask服务器（用于API访问和飞书Webhook）"""
        try:
            # 检查依赖
            try:
                import flask
                import flask_cors
            except ImportError:
                print("Flask未安装，workflow API将不可用")
                return
            
            # 在后台线程中启动Flask服务器
            def run_workflow_server():
                import logging
                import time
                from datetime import datetime
                
                # 配置日志
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                logger = logging.getLogger(__name__)
                
                max_retries = 5
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        from flask import Flask, request
                        from flask_cors import CORS
                        from feature.feishu.backend.api.workflow_api import workflow_api
                        from pathlib import Path
                        import os
                        
                        # 获取workflow目录（使用项目根目录）
                        current_project_root = Path(os.path.dirname(os.path.abspath(__file__)))
                        workflow_dir = current_project_root / "feature" / "workflow"
                        
                        # 创建Flask应用
                        app = Flask(__name__, 
                                  static_folder=str(workflow_dir / 'static'),
                                  static_url_path='/static')
                        CORS(app)
                        
                        # 添加请求日志中间件
                        @app.before_request
                        def log_request_info():
                            if request.path.startswith('/api/'):
                                logger.info(f"收到请求: {request.method} {request.path}")
                                if request.path == '/api/feishu-webhook':
                                    logger.info(f"飞书Webhook请求来源: {request.remote_addr}")
                        
                        # 注册蓝图
                        app.register_blueprint(workflow_api, url_prefix='/api')
                        
                        # 添加根路由
                        @app.route('/')
                        def index():
                            return app.send_static_file('index.html')
                        
                        # 启动服务器
                        port = 5012
                        logger.info(f"Workflow API服务器启动中...")
                        logger.info(f"飞书Webhook地址: http://0.0.0.0:{port}/api/feishu-webhook")
                        logger.info(f"Web界面地址: http://localhost:{port}/")
                        logger.info(f"服务器已启动，正在监听端口 {port}，等待飞书Webhook请求...")
                        print(f"Workflow API服务器已启动在端口 {port}")
                        print(f"飞书Webhook地址: http://0.0.0.0:{port}/api/feishu-webhook")
                        print(f"Web界面地址: http://localhost:{port}/")
                        print(f"服务器正在运行，随时准备接收飞书Webhook请求")
                        
                        # 重置重试计数（成功启动）
                        retry_count = 0
                        
                        # 启动服务器（阻塞调用）
                        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
                        
                    except OSError as e:
                        if "Address already in use" in str(e):
                            logger.error(f"端口 {port} 已被占用，请检查是否有其他程序在使用该端口")
                            print(f"端口 {port} 已被占用")
                            break  # 端口被占用，不重试
                        else:
                            retry_count += 1
                            logger.error(f"启动Workflow API服务器失败 (尝试 {retry_count}/{max_retries}): {e}")
                            if retry_count < max_retries:
                                wait_time = min(2 ** retry_count, 30)  # 指数退避，最多30秒
                                logger.info(f"{wait_time}秒后重试...")
                                time.sleep(wait_time)
                            else:
                                logger.error(f"达到最大重试次数，停止尝试启动服务器")
                                break
                    except Exception as e:
                        retry_count += 1
                        import traceback
                        logger.error(f"启动Workflow API服务器失败 (尝试 {retry_count}/{max_retries}): {e}")
                        traceback.print_exc()
                        if retry_count < max_retries:
                            wait_time = min(2 ** retry_count, 30)
                            logger.info(f"{wait_time}秒后重试...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"达到最大重试次数，停止尝试启动服务器")
                            break
            
            # 在后台线程中运行服务器
            server_thread = threading.Thread(target=run_workflow_server, daemon=True, name="WorkflowServer")
            server_thread.start()
            
            # 不阻塞主线程，让服务器在后台启动
            # 服务器会在后台线程中自动启动，不会影响主应用的响应
            
        except Exception as e:
            print(f"启动Workflow API服务器时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    @rumps.clicked("文件复制器")
    def open_file_duplicator(self, _):
        """打开文件复制器"""
        try:
            print("正在打开文件复制器...")
            self.file_duplicator_manager.open_feature()
            print("文件复制器已打开")
        except Exception as e:
            print(f"打开文件复制器失败: {str(e)}")
            rumps.alert("错误", f"打开文件复制器失败: {str(e)}")
    
        
    
    @rumps.clicked("Schema生成器")
    def open_schema_generator(self, _):
        """打开Schema生成器"""
        try:
            print("正在打开Schema生成器...")
            self.schema_generator_manager.open_feature()
            print("Schema生成器已打开")
        except Exception as e:
            print(f"打开Schema生成器失败: {str(e)}")
            rumps.alert("错误", f"打开Schema生成器失败: {str(e)}")
    
    @rumps.clicked("命令大全")
    def open_command_tool(self, _):
        """打开命令大全"""
        try:
            print("正在打开命令大全...")
            self.command_tool_manager.open_feature()
            print("命令大全已打开")
        except Exception as e:
            print(f"打开命令大全失败: {str(e)}")
            rumps.alert("错误", f"打开命令大全失败: {str(e)}")
    
    @rumps.clicked("数据脚本生成器")
    def open_data_script_generator(self, _):
        """打开数据脚本生成器"""
        try:
            print("正在打开数据脚本生成器...")
            self.data_script_generator_manager.open_feature()
            print("数据脚本生成器已打开")
        except Exception as e:
            print(f"打开数据脚本生成器失败: {str(e)}")
            rumps.alert("错误", f"打开数据脚本生成器失败: {str(e)}")
    
    @rumps.clicked("Workflow可视化")
    def open_workflow_visualizer(self, _):
        """打开Workflow可视化工具"""
        try:
            print("正在打开Workflow可视化工具...")
            import traceback
            self.workflow_visualizer_manager.open_feature()
            print("Workflow可视化工具已打开")
        except Exception as e:
            import traceback
            error_msg = f"打开Workflow可视化工具失败: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            rumps.alert("错误", error_msg)


def main():
    """主函数"""
    print("dd_fast 多功能工具集")
    print("=" * 50)
    
    try:
        print("启动 dd_fast 系统托盘应用...")
        print("应用将在系统托盘运行")
        print("右键点击托盘图标查看功能菜单")
        app = DDFastApp()
        app.run()
    except Exception as e:
        print(f"启动失败: {e}")
        print("请检查依赖是否正确安装")
        sys.exit(1)


if __name__ == "__main__":
    main()
