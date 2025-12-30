#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dd_fast - Flask API服务器
直接启动Flask服务器，提供API和Webhook功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入server.py中的启动函数
from server import run_server


def main():
    """主函数"""
    print("dd_fast Flask API服务器")
    print("=" * 50)
    
    try:
        print("启动 dd_fast 服务器...")
        print("服务器将在后台运行，提供API和Webhook功能")
        run_server(host='0.0.0.0', port=5012, debug=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
