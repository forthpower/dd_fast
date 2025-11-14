#!/usr/bin/env python3
"""
Primer Workflow 可视化编辑器启动脚本
启动本地HTTP服务器来运行可视化工具
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def start_server(port=8000):
    """启动HTTP服务器"""
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 创建HTTP服务器
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"🚀 Primer Workflow 可视化编辑器已启动!")
            print(f"🌐 演示页面: http://localhost:{port}/explorer-demo.html")
            print(f"🛠️  可视化编辑器: http://localhost:{port}/workflow-explorer.html")
            print("="*60 + "\n")
            
            # 自动打开浏览器
            try:
                webbrowser.open(f"http://localhost:{port}/explorer-demo.html")
            except:
                pass
            
            # 启动服务器
            httpd.serve_forever()
            
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ 端口 {port} 已被占用，尝试使用端口 {port + 1}")
            start_server(port + 1)
        else:
            print(f"❌ 启动服务器失败: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        sys.exit(0)

def check_files():
    """检查必要文件是否存在"""
    required_files = [
        "workflow-explorer.html",
        "workflow-explorer.js", 
        "explorer-demo.html",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少以下必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n请确保所有文件都在当前目录中")
        return False
    
    print("✅ 所有必要文件检查通过")
    return True

def main():
    """主函数"""
    print("🎯 Primer Workflow 可视化编辑器")
    print("=" * 40)
    
    # 检查文件
    if not check_files():
        sys.exit(1)
    
    # 获取端口号
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的端口号，使用默认端口 8000")
    
    # 启动服务器
    start_server(port)

if __name__ == "__main__":
    main()
