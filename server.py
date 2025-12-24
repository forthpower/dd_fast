#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dd_fast 服务器启动脚本（Linux版本）
用于在Linux服务器上运行Flask API服务，不依赖系统托盘
"""

import sys
import os
import logging
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "server.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def create_flask_app():
    """创建Flask应用"""
    try:
        from flask import Flask, request
        from flask_cors import CORS
        from feature.feishu.backend.api.workflow_api import workflow_api
        
        # 获取workflow目录
        workflow_dir = project_root / "feature" / "workflow"
        
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
        
        return app
        
    except ImportError as e:
        logger.error(f"导入依赖失败: {e}")
        logger.error("请确保已安装所有依赖: pip3 install -r requirements.txt")
        raise
    except Exception as e:
        logger.error(f"创建Flask应用失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def run_server(host='0.0.0.0', port=5012, debug=False):
    """运行Flask服务器"""
    max_retries = 5
    retry_count = 0
    
    logger.info("=" * 60)
    logger.info("dd_fast 服务器启动")
    logger.info(f"项目目录: {project_root}")
    logger.info(f"日志目录: {log_dir}")
    logger.info("=" * 60)
    
    while retry_count < max_retries:
        try:
            app = create_flask_app()
            
            logger.info(f"Workflow API服务器启动中...")
            logger.info(f"监听地址: {host}:{port}")
            logger.info(f"飞书Webhook地址: http://{host}:{port}/api/feishu-webhook")
            logger.info(f"健康检查地址: http://{host}:{port}/api/health")
            logger.info(f"Web界面地址: http://{host}:{port}/")
            logger.info(f"服务器已启动，正在监听端口 {port}，等待请求...")
            
            # 重置重试计数（成功启动）
            retry_count = 0
            
            # 启动服务器（阻塞调用）
            app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
            
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error(f"端口 {port} 已被占用，请检查是否有其他程序在使用该端口")
                logger.error("可以使用以下命令查看占用端口的进程:")
                logger.error(f"  lsof -i :{port} 或 netstat -tulpn | grep {port}")
                break  # 端口被占用，不重试
            else:
                retry_count += 1
                logger.error(f"启动服务器失败 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 30)  # 指数退避，最多30秒
                    logger.info(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"达到最大重试次数，停止尝试启动服务器")
                    break
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭服务器...")
            break
        except Exception as e:
            retry_count += 1
            import traceback
            logger.error(f"启动服务器失败 (尝试 {retry_count}/{max_retries}): {e}")
            traceback.print_exc()
            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 30)
                logger.info(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"达到最大重试次数，停止尝试启动服务器")
                break
    
    logger.info("服务器已关闭")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='dd_fast 服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5012, help='监听端口 (默认: 5012)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    try:
        run_server(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

