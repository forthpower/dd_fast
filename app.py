#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dd_fast 文件复制器
桌面应用程序
"""

import tkinter as tk
from tkinter import messagebox
import sys
from feature.file_duplicator import Feature

class DesktopApp:
    """桌面应用程序主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("dd_fast - 文件复制器")
        self.root.geometry("600x400")
        self.root.configure(bg='#2c3e50')
        
        # 设置窗口居中显示
        self.center_window()
        
        # 初始化功能模块
        self.file_duplicator = Feature()
        
        # 创建主界面
        self.create_main_interface()
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_main_interface(self):
        """创建主界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)
        
        # 标题区域
        title_frame = tk.Frame(main_container, bg='#2c3e50')
        title_frame.pack(fill=tk.X, pady=(0, 50))
        
        # 主标题
        title_label = tk.Label(
            title_frame, 
            text="dd_fast", 
            font=("Arial", 36, "bold"),
            bg='#2c3e50', 
            fg='#ecf0f1'
        )
        title_label.pack()
        
        # 主功能按钮区域
        button_frame = tk.Frame(main_container, bg='#2c3e50')
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建主功能按钮
        self.create_main_button(button_frame)
        
        # 底部信息区域
        info_frame = tk.Frame(main_container, bg='#2c3e50')
        info_frame.pack(fill=tk.X, pady=(40, 0))
        
        info_label = tk.Label(
            info_frame, 
            text="版本 1.0 | dd_fast 多功能工具", 
            font=("Arial", 12),
            bg='#2c3e50', 
            fg='#95a5a6'
        )
        info_label.pack()
    
    def create_main_button(self, parent):
        """创建主功能按钮"""
        # 按钮容器
        button_container = tk.Frame(parent, bg='#2c3e50')
        button_container.pack(expand=True)
        
        # 主功能按钮
        main_button = tk.Button(
            button_container,
            text="🚀 开始使用文件复制器",
            command=self.open_file_duplicator,
            font=("Arial", 20, "bold"),
            bg='#3498db',
            fg='black',
            relief='flat',
            width=25,
            height=3,
            cursor='hand2',
            bd=0,
            highlightthickness=0
        )
        main_button.pack(pady=40)
        
        # 添加悬停效果
        self.add_button_hover_effect(main_button, '#3498db', '#2980b9')
    
    def add_button_hover_effect(self, button, original_color, hover_color):
        """为按钮添加悬停效果"""
        def on_enter(event):
            button.config(bg=hover_color)
        
        def on_leave(event):
            button.config(bg=original_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
    
    def open_file_duplicator(self):
        """打开文件复制器"""
        try:
            self.file_duplicator.showFileDuplicator()
            if self.file_duplicator.window is not None:
                # 设置窗口关闭时的处理
                self.file_duplicator.window.protocol("WM_DELETE_WINDOW", self.on_file_duplicator_close)
        except Exception as e:
            messagebox.showerror("错误", f"打开文件复制器时出错: {str(e)}")
    
    def on_file_duplicator_close(self):
        """文件复制器窗口关闭时的处理"""
        if self.file_duplicator.window:
            self.file_duplicator.window.withdraw()
    
    def run(self):
        """运行应用程序"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动主循环
        self.root.mainloop()
    
    def on_closing(self):
        """应用程序关闭时的处理"""
        # 清理资源
        if hasattr(self, 'file_duplicator') and self.file_duplicator.window:
            self.file_duplicator.cleanup()
        
        # 退出应用程序
        self.root.destroy()
        sys.exit(0)

def main():
    """主函数"""
    try:
        app = DesktopApp()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"应用程序启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
