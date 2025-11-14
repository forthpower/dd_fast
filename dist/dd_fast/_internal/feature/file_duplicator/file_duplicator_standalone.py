#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件复制器独立启动脚本
在独立进程中运行，避免与系统托盘应用冲突
"""

import sys
import os
import tkinter as tk

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from feature.file_duplicator.file_duplicator import Feature

def main():
    """主函数"""
    try:
        print("🚀 启动文件复制器...")
        
        # 创建Tkinter应用
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        # 创建文件复制器功能
        feature = Feature()
        
        # 显示文件复制器窗口
        feature.showFileDuplicator()
        
        # 运行主循环
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 启动文件复制器失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
