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
            self.window = tk.Tk()
            self.window.title("文件批量复制器")
            self.window.geometry("1000x900")
            self.window.configure(bg='#f0f0f0')
            
            # 设置窗口居中
            self.center_window()
            
            self.setupWindow()
        
        self.window.deiconify()
        self.window.lift()
    
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
        title_label = tk.Label(self.window, text="文件批量复制器", font=("Arial", 20, "bold"),
                              bg='#f0f0f0', fg='#000000')
        title_label.pack(pady=15)
        
        # 主框架
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 目录选择框架
        dir_frame = tk.LabelFrame(main_frame, text="目标目录", font=("Arial", 12, "bold"),
                                 bg='#f0f0f0', fg='#000000')
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        dir_select_frame = tk.Frame(dir_frame, bg='#f0f0f0')
        dir_select_frame.pack(fill=tk.X, padx=10, pady=8)
        
        self.dir_label = tk.Label(dir_select_frame, text="未选择目录", bg='#f0f0f0', fg='#000000', font=("Arial", 12))
        self.dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        dir_btn = tk.Button(dir_select_frame, text="选择目录", command=self.selectDirectory,
                           bg='#4CAF50', fg='black', relief='flat', font=("Arial", 13, "bold"))
        dir_btn.pack(side=tk.RIGHT, padx=(15, 0))
        
        # 文件选择框架
        file_frame = tk.LabelFrame(main_frame, text="选择文件", font=("Arial", 12, "bold"),
                                  bg='#f0f0f0', fg='#000000')
        file_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 文件列表
        file_list_frame = tk.Frame(file_frame, bg='#f0f0f0')
        file_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # 文件列表和滚动条
        list_frame = tk.Frame(file_list_frame, bg='#f0f0f0')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, bg='white', fg='#000000', font=("Arial", 12))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件操作按钮
        file_btn_frame = tk.Frame(file_frame, bg='#f0f0f0')
        file_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        
        select_files_btn = tk.Button(file_btn_frame, text="选择文件", command=self.selectFiles,
                                    bg='#2196F3', fg='black', relief='flat', font=("Arial", 13, "bold"))
        select_files_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        scan_files_btn = tk.Button(file_btn_frame, text="扫描目录", command=self.scanDirectory,
                                  bg='#FF9800', fg='black', relief='flat', font=("Arial", 13, "bold"))
        scan_files_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        clear_btn = tk.Button(file_btn_frame, text="清空列表", command=self.clearFileList,
                             bg='#f44336', fg='black', relief='flat', font=("Arial", 13, "bold"))
        clear_btn.pack(side=tk.LEFT)
        
        # 语言选择框架
        lang_frame = tk.LabelFrame(main_frame, text="语言设置", font=("Arial", 12, "bold"),
                                  bg='#f0f0f0', fg='#000000')
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 全选/全不选按钮（放在顶部，更显眼）
        lang_btn_frame = tk.Frame(lang_frame, bg='#f0f0f0')
        lang_btn_frame.pack(fill=tk.X, padx=10, pady=(8, 5))
        
        select_all_btn = tk.Button(lang_btn_frame, text="✅ 全选", command=self.selectAllLanguages,
                                  bg='#4CAF50', fg='black', relief='flat', font=("Arial", 13, "bold"),
                                  width=10, height=2)
        select_all_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        deselect_all_btn = tk.Button(lang_btn_frame, text="❌ 全不选", command=self.deselectAllLanguages,
                                    bg='#f44336', fg='black', relief='flat', font=("Arial", 13, "bold"),
                                    width=10, height=2)
        deselect_all_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # 语言复选框框架
        lang_check_frame = tk.Frame(lang_frame, bg='#f0f0f0')
        lang_check_frame.pack(fill=tk.X, padx=10, pady=(5, 8))
        
        # 创建语言复选框（分两列）
        self.language_vars = {}
        row = 0
        col = 0
        
        for lang_code, lang_name in LANGUAGE_CODES.items():
            var = tk.BooleanVar(value=True)  # 默认选中
            self.language_vars[lang_code] = var
            
            cb = tk.Checkbutton(lang_check_frame, text=f"{lang_code} - {lang_name}",
                               variable=var, bg='#f0f0f0', fg='#000000', font=("Arial", 11),
                               selectcolor='#4CAF50', activebackground='#e8f5e8')
            cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            
            col += 1
            if col >= 3:  # 每行3个
                col = 0
                row += 1
        
        # 操作按钮框架
        action_frame = tk.Frame(main_frame, bg='#f0f0f0')
        action_frame.pack(fill=tk.X, pady=(10, 10))
        
        preview_btn = tk.Button(action_frame, text="🔍 预览", command=self.previewOperation,
                               bg='#9C27B0', fg='black', relief='flat', font=("Arial", 14, "bold"),
                               width=12, height=2)
        preview_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        execute_btn = tk.Button(action_frame, text="🚀 执行复制", command=self.executeOperation,
                               bg='#4CAF50', fg='black', relief='raised', font=("Arial", 16, "bold"),
                               width=15, height=2, bd=3, highlightthickness=3)
        execute_btn.pack(side=tk.LEFT)
        
        # 结果显示框架
        result_frame = tk.LabelFrame(main_frame, text="操作结果", font=("Arial", 12, "bold"),
                                    bg='#f0f0f0', fg='#000000')
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=6, bg='white', fg='#000000', font=("Arial", 11))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
    
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
    
    def scanDirectory(self):
        """扫描目录中的文件"""
        if not self.target_directory:
            messagebox.showwarning("警告", "请先选择目标目录")
            return
        
        # 清空现有列表
        self.clearFileList()
        
        # 扫描目录
        for file_path in self.target_directory.iterdir():
            if file_path.is_file():
                file_name = file_path.name
                self.selected_files.append(file_name)
                self.file_listbox.insert(tk.END, file_name)
    
    def clearFileList(self):
        """清空文件列表"""
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)
    
    def selectAllLanguages(self):
        """全选语言"""
        for var in self.language_vars.values():
            var.set(True)
        # 强制刷新界面
        self.window.update()
        # 显示提示信息
        self.result_text.insert(tk.END, "✅ 已全选所有语言\n")
        self.result_text.see(tk.END)
    
    def deselectAllLanguages(self):
        """全不选语言"""
        for var in self.language_vars.values():
            var.set(False)
        # 强制刷新界面
        self.window.update()
        # 显示提示信息
        self.result_text.insert(tk.END, "❌ 已取消选择所有语言\n")
        self.result_text.see(tk.END)
    
    def getSelectedLanguages(self):
        """获取选中的语言"""
        selected = []
        for lang_code, var in self.language_vars.items():
            if var.get():
                selected.append(lang_code)
        return selected
    
    def previewOperation(self):
        """预览操作"""
        if not self.target_directory or not self.selected_files:
            messagebox.showwarning("警告", "请选择目录和文件")
            return
        
        selected_languages = self.getSelectedLanguages()
        if not selected_languages:
            messagebox.showwarning("警告", "请至少选择一个语言")
            return
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "预览模式 - 以下文件将被创建:\n\n")
        
        for file_name in self.selected_files:
            file_path = self.target_directory / file_name
            if file_path.exists():
                file_info = self._analyze_filename(file_name)
                
                for lang_code in selected_languages:
                    new_name = self._generate_filename(file_info, lang_code)
                    target_path = self.target_directory / new_name
                    
                    status = "已存在" if target_path.exists() else "将创建"
                    self.result_text.insert(tk.END, f"  {file_name} -> {new_name} ({status})\n")
    
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
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "开始执行复制操作...\n\n")
        
        total_created = 0
        total_skipped = 0
        total_failed = 0
        
        for file_name in self.selected_files:
            file_path = self.target_directory / file_name
            if not file_path.exists():
                self.result_text.insert(tk.END, f"❌ 文件不存在: {file_name}\n")
                total_failed += 1
                continue
            
            try:
                file_info = self._analyze_filename(file_name)
                
                for lang_code in selected_languages:
                    try:
                        new_name = self._generate_filename(file_info, lang_code)
                        target_path = self.target_directory / new_name
                        
                        if target_path.exists():
                            self.result_text.insert(tk.END, f"⏭️  跳过: {new_name} (已存在)\n")
                            total_skipped += 1
                            continue
                        
                        # 复制文件
                        shutil.copy2(file_path, target_path)
                        self.result_text.insert(tk.END, f"✅ 创建: {new_name}\n")
                        total_created += 1
                        
                    except Exception as e:
                        self.result_text.insert(tk.END, f"❌ 失败: {new_name} - {str(e)}\n")
                        total_failed += 1
                        
            except Exception as e:
                self.result_text.insert(tk.END, f"❌ 处理文件失败: {file_name} - {str(e)}\n")
                total_failed += 1
        
        # 显示统计结果
        self.result_text.insert(tk.END, f"\n操作完成!\n")
        self.result_text.insert(tk.END, f"成功创建: {total_created} 个文件\n")
        self.result_text.insert(tk.END, f"跳过文件: {total_skipped} 个\n")
        self.result_text.insert(tk.END, f"失败: {total_failed} 个\n")
        
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
