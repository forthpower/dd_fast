#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令大全功能
提供可视化的命令执行界面，支持顺序执行多个终端命令
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import time
import os
import sys
from pathlib import Path


class CommandTool:
    """命令大全工具类"""
    
    def __init__(self):
        self.window = None
        self.commands = []
        self.current_index = 0
        self.is_running = False
        self.output_text = None
        self.progress_var = None
        self.status_label = None
        
    def showCommandTool(self):
        """显示命令大全界面"""
        if self.window is None or not self.window.winfo_exists():
            # 创建独立的Tkinter窗口
            self.window = tk.Tk()
            self.window.geometry("600x320")
            
            # 设置明亮的颜色主题
            self.window.configure(bg='#f8f9fa')
            
            # 设置窗口图标和样式
            self.window.resizable(False, False)
            
            # 设置窗口居中
            self.center_window()
            
            # 设置窗口关闭事件
            self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            # 创建界面（精简为单按钮）
            self.create_interface()
        
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
    
    def on_window_close(self):
        """窗口关闭时的处理"""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def center_window(self):
        """窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_interface(self):
        """创建界面（单按钮：国际跳板机）"""
        main_frame = tk.Frame(self.window, bg='#f8f9fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        title_label = tk.Label(
            main_frame,
            text="⚡ 命令大全",
            font=("Arial", 26, "bold"),
            bg='#f8f9fa',
            fg='#2c3e50'
        )
        title_label.pack(pady=(10, 6))

        btn = tk.Button(
            main_frame,
            text="国际跳板机",
            command=self.open_jumpserver_global,
            font=("Arial", 18, "bold"),
            bg='#3498db',
            fg='black',
            activeforeground='black',
            relief='flat',
            bd=0,
            padx=28,
            pady=14,
            cursor='hand2'
        )
        btn.pack(pady=10)

        btn = tk.Button(
            main_frame,
            text="国内跳板机",
            command=self.open_jumpserver_cn,
            font=("Arial", 18, "bold"),
            bg='#3498db',
            fg='black',
            activeforeground='black',
            relief='flat',
            bd=0,
            padx=28,
            pady=14,
            cursor='hand2'
        )
        btn.pack(pady=10)

    def open_jumpserver_global(self):
        """在macOS终端中打开跳板机SSH会话"""
        try:
            ssh_cmd = "ssh -i ~/.ssh/id_rsa -p 63008 yongjian.dai@dd-jumpserver.centurygame.com"
            applescript = (
                'tell application "Terminal"\n'
                '    activate\n'
                f'    do script "{ssh_cmd}"\n'
                'end tell\n'
            )
            subprocess.run(["osascript", "-e", applescript], check=True)
        except Exception as e:
            messagebox.showerror("错误", f"打开终端失败: {e}")

    def open_jumpserver_cn(self):
        """在macOS终端中打开跳板机SSH会话"""
        try:
            ssh_cmd = "ssh -i ~/.ssh/id_rsa -p 63008 yongjian.dai@dd-cn-jumpserver.campfiregames.cn"
            applescript = (
                'tell application "Terminal"\n'
                '    activate\n'
                f'    do script "{ssh_cmd}"\n'
                'end tell\n'
            )
            subprocess.run(["osascript", "-e", applescript], check=True)
        except Exception as e:
            messagebox.showerror("错误", f"打开终端失败: {e}")
