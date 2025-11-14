#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件批量复制和重命名功能
支持根据语言代码批量复制文件并重命名
"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Dict

# 支持的语言代码映射
LANGUAGE_CODES = {
    "en": "英语",
    "de": "德语", 
    "fr": "法语",
    "ja": "日语",
    "ko": "韩语",
    "zh-hant": "繁中",
    "zh-hans": "简中",
    "es": "西班牙语",
    "th": "泰语",
    "id": "印尼语",
    "ru": "俄语",
    "ar": "阿拉伯语",
    "vi": "越南语",
    "pt": "葡萄牙语",
    "tr": "土耳其语",
    "it": "意大利语",
    "nl": "荷兰语",
    "pl": "波兰语"
}


class Feature:
    """文件批量复制功能类"""
    
    def __init__(self):
        self.name = "文件复制器"
        self.window = None
        self.target_directory = None
        self.selected_files = []
    
    def showFileDuplicator(self, icon=None, item=None):
        """显示文件复制器窗口"""
        if self.window is None or not self.window.winfo_exists():
            # 创建独立的Tkinter窗口
            self.window = tk.Tk()
            self.window.title("🚀 文件批量复制器")
            self.window.geometry("700x550")
            
            # 设置明亮的颜色主题
            self.window.configure(bg='#f8f9fa')
            
            # 设置窗口图标和样式
            self.window.resizable(True, True)
            self.window.minsize(600, 650)
            
            # 设置窗口居中
            self.center_window()
            
            # 设置窗口关闭事件
            self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
            
            self.setupWindow()
        
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
    
    def on_window_close(self):
        """窗口关闭时的处理"""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def setupWindow(self):
        """设置窗口内容"""
        # 标题
        title_label = tk.Label(self.window, text="🚀 文件批量复制器", 
                              font=("Arial", 24, "bold"),
                              bg='#f8f9fa', fg='#2c3e50')
        title_label.pack(pady=(20, 10))
        
        # 副标题
        subtitle_label = tk.Label(self.window, text="批量生成多语言命名的文件副本", 
                                 font=("Arial", 12),
                                 bg='#f8f9fa', fg='#6c757d')
        subtitle_label.pack(pady=(0, 20))
        
        # 主框架
        main_frame = tk.Frame(self.window, bg='#f8f9fa')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=(0, 20))
        
        # 第一行：目录选择和文件选择
        first_row = tk.Frame(main_frame, bg='#f8f9fa')
        first_row.pack(fill=tk.X, pady=(0, 15))
        
        # 目录选择框架
        dir_frame = tk.LabelFrame(first_row, text="📁 目标目录", font=("Arial", 13, "bold"),
                                 bg='#ffffff', fg='#2c3e50', relief='groove', bd=2)
        dir_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        
        dir_select_frame = tk.Frame(dir_frame, bg='#ffffff')
        dir_select_frame.pack(fill=tk.X, padx=12, pady=8)
        
        self.dir_label = tk.Label(dir_select_frame, text="未选择目录", 
                                 bg='#ffffff', fg='#6c757d', font=("Arial", 11))
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        dir_btn = tk.Button(
            dir_select_frame,
            text="📂 选择目录",
            command=self.selectDirectory,
            bg='#3498db',
            fg='black',
            activeforeground='white',
            disabledforeground='#eeeeee',
            relief='flat',
            font=("Arial", 11, "bold"),
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            highlightthickness=0
        )
        dir_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 添加悬停效果
        def on_enter_dir_btn(e):
            dir_btn.config(bg='#2980b9')
        def on_leave_dir_btn(e):
            dir_btn.config(bg='#3498db')
        dir_btn.bind("<Enter>", on_enter_dir_btn)
        dir_btn.bind("<Leave>", on_leave_dir_btn)
        
        # 文件选择框架
        file_frame = tk.LabelFrame(first_row, text="📄 选择文件", font=("Arial", 13, "bold"),
                                  bg='#ffffff', fg='#2c3e50', relief='groove', bd=2)
        file_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        
        # 文件列表
        file_list_frame = tk.Frame(file_frame, bg='#ffffff')
        file_list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # 文件列表和滚动条
        list_frame = tk.Frame(file_list_frame, bg='#ffffff')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, 
                                      bg='white', fg='#2c3e50', font=("Arial", 10),
                                      selectbackground='#3498db', selectforeground='white',
                                      relief='sunken', bd=1)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件操作按钮
        file_btn_frame = tk.Frame(file_frame, bg='#ffffff')
        file_btn_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
        
        select_files_btn = tk.Button(
            file_btn_frame,
            text="📎 选择文件",
            command=self.selectFiles,
            bg='#e74c3c',
            fg='black',
            activeforeground='white',
            disabledforeground='#eeeeee',
            relief='flat',
            font=("Arial", 11, "bold"),
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            highlightthickness=0
        )
        select_files_btn.pack(side=tk.LEFT)
        
        # 添加悬停效果
        def on_enter_file_btn(e):
            select_files_btn.config(bg='#c0392b')
        def on_leave_file_btn(e):
            select_files_btn.config(bg='#e74c3c')
        select_files_btn.bind("<Enter>", on_enter_file_btn)
        select_files_btn.bind("<Leave>", on_leave_file_btn)
        
        # 第二行：语言设置、操作、操作结果
        second_row = tk.Frame(main_frame, bg='#f8f9fa')
        second_row.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 语言选择框架
        lang_frame = tk.LabelFrame(second_row, text="🌍 语言设置", font=("Arial", 13, "bold"),
                                  bg='#ffffff', fg='#2c3e50', relief='groove', bd=2)
        lang_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        
        # 语言复选框框架
        lang_check_frame = tk.Frame(lang_frame, bg='#ffffff')
        lang_check_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # 创建语言复选框（分两列）
        self.language_vars = {}
        self.language_checkboxes = {}  # 存储复选框引用
        row = 0
        col = 0
        
        for lang_code, lang_name in LANGUAGE_CODES.items():
            var = tk.BooleanVar(value=True)  # 默认选中
            self.language_vars[lang_code] = var
            
            cb = tk.Checkbutton(lang_check_frame, text=f"{lang_code} - {lang_name}",
                               variable=var, bg='#ffffff', fg='#2c3e50', font=("Arial", 10),
                               selectcolor='#27ae60', activebackground='#ffffff',
                               activeforeground='#2c3e50', onvalue=True, offvalue=False,
                               relief='flat', bd=0)
            cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            
            # 存储复选框引用
            self.language_checkboxes[lang_code] = cb
            
            col += 1
            if col >= 2:  # 每行2个，更紧凑
                col = 0
                row += 1
        
        # 操作按钮框架
        action_frame = tk.LabelFrame(second_row, text="⚡ 操作", font=("Arial", 13, "bold"),
                                    bg='#ffffff', fg='#2c3e50', relief='groove', bd=2)
        action_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        
        # 操作按钮容器
        action_btn_frame = tk.Frame(action_frame, bg='#ffffff')
        action_btn_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # 全选/全不选按钮
        select_all_btn = tk.Button(
            action_btn_frame,
            text="✅ 全选",
            command=self.selectAllLanguages,
            bg='#27ae60',
            fg='black',
            activeforeground='white',
            disabledforeground='#eeeeee',
            relief='flat',
            font=("Arial", 11, "bold"),
            bd=0,
            padx=10,
            pady=8,
            cursor='hand2',
            highlightthickness=0
        )
        select_all_btn.pack(fill=tk.X, pady=(0, 8))
        
        deselect_all_btn = tk.Button(
            action_btn_frame,
            text="❌ 全不选",
            command=self.deselectAllLanguages,
            bg='#e74c3c',
            fg='black',
            activeforeground='white',
            disabledforeground='#eeeeee',
            relief='flat',
            font=("Arial", 11, "bold"),
            bd=0,
            padx=10,
            pady=8,
            cursor='hand2',
            highlightthickness=0
        )
        deselect_all_btn.pack(fill=tk.X, pady=(0, 15))
        
        # 分隔线
        separator = tk.Frame(action_btn_frame, height=2, bg='#dee2e6')
        separator.pack(fill=tk.X, pady=8)
        
        execute_btn = tk.Button(
            action_btn_frame,
            text="🚀 执行复制",
            command=self.executeOperation,
            bg='#f39c12',
            fg='black',
            activeforeground='white',
            disabledforeground='#eeeeee',
            relief='flat',
            font=("Arial", 13, "bold"),
            bd=0,
            padx=15,
            pady=12,
            cursor='hand2',
            highlightthickness=0
        )
        execute_btn.pack(fill=tk.X)
        
        # 添加悬停效果
        def on_enter_select_all(e):
            select_all_btn.config(bg='#229954')
        def on_leave_select_all(e):
            select_all_btn.config(bg='#27ae60')
        select_all_btn.bind("<Enter>", on_enter_select_all)
        select_all_btn.bind("<Leave>", on_leave_select_all)
        
        def on_enter_deselect_all(e):
            deselect_all_btn.config(bg='#c0392b')
        def on_leave_deselect_all(e):
            deselect_all_btn.config(bg='#e74c3c')
        deselect_all_btn.bind("<Enter>", on_enter_deselect_all)
        deselect_all_btn.bind("<Leave>", on_leave_deselect_all)
        
        def on_enter_execute(e):
            execute_btn.config(bg='#e67e22')
        def on_leave_execute(e):
            execute_btn.config(bg='#f39c12')
        execute_btn.bind("<Enter>", on_enter_execute)
        execute_btn.bind("<Leave>", on_leave_execute)
    
    def selectDirectory(self):
        """选择目标目录"""
        directory = filedialog.askdirectory(title="选择目标目录")
        if directory:
            self.target_directory = Path(directory)
            self.dir_label.config(text=str(self.target_directory), fg='#000000')
            self.scanDirectory()
    
    def selectFiles(self):
        """选择文件"""
        if not self.target_directory:
            messagebox.showwarning("警告", "请先选择目标目录")
            return
        
        files = filedialog.askopenfilenames(
            title="选择要复制的文件",
            initialdir=str(self.target_directory)
        )
        
        for file_path in files:
            file_name = Path(file_path).name
            if file_name not in self.selected_files:
                self.selected_files.append(file_name)
                self.file_listbox.insert(tk.END, file_name)
    
    def selectAllLanguages(self):
        """全选语言"""
        for lang_code, var in self.language_vars.items():
            var.set(True)
            # 直接设置复选框状态
            if lang_code in self.language_checkboxes:
                self.language_checkboxes[lang_code].select()
        # 强制刷新界面
        self.window.update_idletasks()
        self.window.update()
    
    def deselectAllLanguages(self):
        """全不选语言"""
        for lang_code, var in self.language_vars.items():
            var.set(False)
            # 直接设置复选框状态
            if lang_code in self.language_checkboxes:
                self.language_checkboxes[lang_code].deselect()
        # 强制刷新界面
        self.window.update_idletasks()
        self.window.update()
    
    def getSelectedLanguages(self):
        """获取选中的语言"""
        selected = []
        for lang_code, var in self.language_vars.items():
            if var.get():
                selected.append(lang_code)
        return selected
    
    def executeOperation(self):
        """执行复制操作"""
        if not self.target_directory or not self.selected_files:
            messagebox.showwarning("警告", "请选择目录和文件")
            return
        
        selected_languages = self.getSelectedLanguages()
        if not selected_languages:
            messagebox.showwarning("警告", "请至少选择一个语言")
            return
        
        # 确认操作
        result = messagebox.askyesno("确认", f"将为 {len(self.selected_files)} 个文件创建 {len(selected_languages)} 种语言版本，是否继续？")
        if not result:
            return
        
        total_created = 0
        total_skipped = 0
        total_failed = 0
        
        for file_name in self.selected_files:
            file_path = self.target_directory / file_name
            if not file_path.exists():
                total_failed += 1
                continue
            
            try:
                file_info = self._analyze_filename(file_name)
                
                for lang_code in selected_languages:
                    try:
                        new_name = self._generate_filename(file_info, lang_code)
                        target_path = self.target_directory / new_name
                        
                        if target_path.exists():
                            total_skipped += 1
                            continue
                        
                        # 复制文件
                        shutil.copy2(file_path, target_path)
                        total_created += 1
                        
                    except Exception as e:
                        total_failed += 1
                        
            except Exception as e:
                total_failed += 1
        
        # 显示统计结果
        messagebox.showinfo("完成", f"操作完成!\n成功创建: {total_created} 个文件\n跳过: {total_skipped} 个\n失败: {total_failed} 个")
    
    def _analyze_filename(self, filename: str) -> Dict:
        """分析文件名结构"""
        name_parts = filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = '.' + name_parts[1] if len(name_parts) > 1 else ''
        
        # 解析文件名结构
        parts = base_name.split('_')
        
        file_info = {
            "original_name": filename,
            "base_name": base_name,
            "extension": extension,
            "parts": parts,
            "has_description": False,
            "description": "",
            "language": "",
            "platform": ""
        }
        
        if len(parts) >= 3:
            # 检查是否包含平台信息（mobile/pc）
            if parts[-1] in ['mobile', 'pc']:
                file_info["platform"] = parts[-1]
                file_info["language"] = parts[-2]
                
                # 检查是否有描述部分
                if len(parts) > 3:
                    file_info["has_description"] = True
                    file_info["description"] = '_'.join(parts[:-2])
                else:
                    file_info["description"] = parts[0]
            else:
                # 简单格式
                if len(parts) == 3:
                    file_info["language"] = parts[-1]
                    file_info["description"] = parts[0]
        
        return file_info
    
    def _generate_filename(self, file_info: Dict, lang_code: str) -> str:
        """生成新文件名"""
        if file_info["has_description"] and file_info["platform"]:
            # 格式: description_lang_platform.ext
            return f"{file_info['description']}_{lang_code}_{file_info['platform']}{file_info['extension']}"
        elif file_info["platform"]:
            # 格式: basename_lang_platform.ext
            return f"{file_info['description']}_{lang_code}_{file_info['platform']}{file_info['extension']}"
        else:
            # 简单格式: basename_lang.ext
            return f"{file_info['description']}_{lang_code}{file_info['extension']}"
    
    def cleanup(self):
        """清理资源"""
        if self.window:
            self.window.destroy()
            self.window = None


if __name__ == "__main__":
    # 作为独立应用启动
    feature_app = Feature()
    feature_app.showFileDuplicator()
    if feature_app.window is not None:
        feature_app.window.protocol("WM_DELETE_WINDOW", feature_app.cleanup)
        feature_app.window.mainloop()
