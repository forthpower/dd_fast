#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按钮配置文件
统一管理所有功能按钮的文本、字体、颜色等参数
"""

# 主界面按钮配置
MAIN_BUTTONS = {
    "file_duplicator": {
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
    },
    "example_feature": {
        "text": "📝 示例功能",
        "font": ("Arial", 20, "bold"),
        "bg": "#9C27B0",
        "fg": "white",
        "relief": "flat",
        "width": 25,
        "height": 3,
        "cursor": "hand2",
        "bd": 0,
        "highlightthickness": 0
    }
}

# 文件复制器按钮配置
FILE_DUPLICATOR_BUTTONS = {
    "select_directory": {
        "text": "选择目录",
        "font": ("Arial", 12, "bold"),
        "bg": "#4CAF50",
        "fg": "black",
        "relief": "flat"
    },
    "select_files": {
        "text": "选择文件",
        "font": ("Arial", 11, "bold"),
        "bg": "#2196F3",
        "fg": "black",
        "relief": "flat"
    },
    "select_all": {
        "text": "✅ 全选",
        "font": ("Arial", 12, "bold"),
        "bg": "#4CAF50",
        "fg": "black",
        "relief": "flat",
        "width": 12,
        "height": 2
    },
    "deselect_all": {
        "text": "❌ 全不选",
        "font": ("Arial", 12, "bold"),
        "bg": "#f44336",
        "fg": "black",
        "relief": "flat",
        "width": 12,
        "height": 2
    },
    "execute_copy": {
        "text": "🚀 执行复制",
        "font": ("Arial", 14, "bold"),
        "bg": "#4CAF50",
        "fg": "black",
        "relief": "raised",
        "width": 12,
        "height": 2,
        "bd": 2,
        "highlightthickness": 2
    }
}

# 标签配置
LABELS = {
    "main_title": {
        "font": ("Arial", 36, "bold"),
        "bg": "#2c3e50",
        "fg": "#ecf0f1"
    },
    "subtitle": {
        "font": ("Arial", 12),
        "bg": "#2c3e50",
        "fg": "#95a5a6"
    },
    "frame_title": {
        "font": ("Arial", 12, "bold"),
        "bg": "#f0f0f0",
        "fg": "#000000"
    },
    "directory_label": {
        "font": ("Arial", 11),
        "bg": "#f0f0f0",
        "fg": "#000000"
    },
    "checkbox": {
        "font": ("Arial", 10),
        "bg": "#f0f0f0",
        "fg": "#000000",
        "selectcolor": "#4CAF50",
        "activebackground": "#e8f5e8"
    }
}

# 窗口配置
WINDOW_CONFIG = {
    "main": {
        "title": "dd_fast - 文件复制器",
        "geometry": "600x400",
        "bg": "#2c3e50"
    },
    "file_duplicator": {
        "title": "文件批量复制器",
        "geometry": "600x600",
        "bg": "#f0f0f0"
    }
}

# 布局配置
LAYOUT_CONFIG = {
    "main_padding": {"padx": 50, "pady": 50},
    "frame_padding": {"padx": 20, "pady": 10},
    "button_padding": {"pady": 40},
    "title_padding": {"pady": 50}
}
