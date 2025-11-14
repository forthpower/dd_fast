#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令工具管理器
负责与主界面的对接，管理命令大全功能
"""

import tkinter as tk
from tkinter import messagebox
from .command_tool import CommandTool


class CommandToolManager:
    """命令工具管理器"""
    
    def __init__(self):
        self.feature_instance = CommandTool()
        self.button_config = {
            "text": "⚡ 命令大全",
            "font": ("Arial", 20, "bold"),
            "bg": "#E67E22",
            "fg": "black",
            "relief": "flat",
            "width": 25,
            "height": 3,
            "cursor": "hand2",
            "bd": 0,
            "highlightthickness": 0
        }
        self.hover_colors = ('#E67E22', '#D35400')  # (original, hover)

    def get_button_config(self):
        """获取按钮配置"""
        return self.button_config

    def get_hover_colors(self):
        """获取悬停颜色"""
        return self.hover_colors

    def open_feature(self):
        """打开命令大全功能"""
        try:
            import subprocess
            import sys
            import os
            
            # 获取当前脚本的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 在独立进程中启动命令工具
            subprocess.Popen([
                sys.executable, 
                os.path.join(current_dir, "command_tool_standalone.py")
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("✅ 命令工具已在独立进程中启动")
            
        except Exception as e:
            print(f"❌ 打开命令工具时出错: {str(e)}")
            # 如果subprocess失败，尝试原来的方式
            try:
                self.feature_instance.showCommandTool()
                if self.feature_instance.window is not None:
                    self.feature_instance.window.protocol("WM_DELETE_WINDOW", self.on_close)
            except Exception as e2:
                print(f"❌ 备用方式也失败: {str(e2)}")

    def on_close(self):
        """功能关闭时的处理"""
        if self.feature_instance.window:
            self.feature_instance.window.withdraw()

    def cleanup(self):
        """清理资源"""
        if self.feature_instance:
            self.feature_instance.cleanup()
