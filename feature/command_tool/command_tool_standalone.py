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

        # 动态为命令工具添加“重启Docker”按钮功能
        def restart_docker():
            try:
                compose_file = "/Users/centurygame/PycharmProjects/cg-admin-manager/env.d/dev/docker-compose.yml"
                down_cmd = f"docker-compose -f {compose_file} down"
                up_cmd = f"docker-compose -f {compose_file} up"
                applescript = (
                    'tell application "Terminal"\n'
                    '    activate\n'
                    f'    do script "{down_cmd}; {up_cmd}"\n'
                    'end tell\n'
                )
                import subprocess
                subprocess.run(["osascript", "-e", applescript], check=True)
            except Exception as e:
                import tkinter.messagebox as messagebox
                messagebox.showerror("错误", f"重启Docker失败: {e}")

        # 将按钮插入到界面中（在窗口创建后）
        orig_create_interface = command_tool.create_interface

        def wrapped_create_interface():
            orig_create_interface()
            try:
                # 在现有窗口中追加按钮
                # 找到主Frame（按照现有实现，最后一个pack的Frame即为主Frame）
                main_children = command_tool.window.winfo_children()
                if not main_children:
                    return
                main_frame = main_children[0]
                import tkinter as tk
                btn = tk.Button(
                    main_frame,
                    text="重启Docker (cg-admin-manager)",
                    command=restart_docker,
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
            except Exception:
                pass

        command_tool.create_interface = wrapped_create_interface

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
