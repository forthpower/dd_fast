#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令工具独立启动脚本
在独立进程中运行，避免与系统托盘应用冲突
"""

import sys
import os
import tkinter as tk

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from feature.command_tool.command_tool import CommandTool

def main():
    """主函数"""
    try:
        print("🚀 启动命令工具...")

        # 创建Tkinter应用
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        # 创建命令工具
        command_tool = CommandTool()

        # 显示命令工具窗口
        command_tool.showCommandTool()

        # 运行主循环
        root.mainloop()

    except Exception as e:
        print(f"❌ 启动命令工具失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
