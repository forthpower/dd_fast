#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件复制器管理器
负责与主界面的对接
"""

import tkinter as tk
from tkinter import messagebox
from .file_duplicator import Feature as FileDuplicatorFeature


class FileDuplicatorManager:
    """文件复制器管理器"""
    
    def __init__(self):
        self.feature = FileDuplicatorFeature()
    
    def get_button_config(self):
        """获取按钮配置"""
        return {
            "text": "🚀 开始使用文件复制器",
            "font": ("Arial", 20, "bold"),
            "bg": "#3498db",
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
        return "#3498db", "#2980b9"
    
    def open_feature(self):
        """打开文件复制器功能"""
        try:
            import subprocess
            import sys
            import os
            
            # 获取当前脚本的目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 在独立进程中启动文件复制器
            subprocess.Popen([
                sys.executable, 
                os.path.join(current_dir, "file_duplicator_standalone.py")
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            print("✅ 文件复制器已在独立进程中启动")
            
        except Exception as e:
            print(f"❌ 打开文件复制器时出错: {str(e)}")
            # 如果subprocess失败，尝试原来的方式
            try:
                self.feature.showFileDuplicator()
                if self.feature.window is not None:
                    self.feature.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
            except Exception as e2:
                print(f"❌ 备用方式也失败: {str(e2)}")
    
    def on_window_close(self):
        """窗口关闭时的处理"""
        if self.feature.window:
            self.feature.window.withdraw()
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self.feature, 'cleanup'):
            self.feature.cleanup()
