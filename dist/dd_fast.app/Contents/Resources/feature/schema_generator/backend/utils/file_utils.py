"""
文件处理工具模块
处理文件扫描、导入等操作
"""

import os
import shutil
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def scan_folder_recursively(
        folder_path: str,
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        递归扫描文件夹中的所有Python文件

        Args:
            folder_path: 文件夹路径

        Returns:
            Tuple[py_files, skipped_files, processed_dirs]
            - py_files: 找到的Python文件列表
            - skipped_files: 跳过的文件列表
            - processed_dirs: 处理的文件夹列表
        """
        py_files = []
        skipped_files = []
        processed_dirs = []

        for root, dirs, files in os.walk(folder_path):
            # 记录进入的文件夹
            rel_path = os.path.relpath(root, folder_path)
            if rel_path != ".":
                processed_dirs.append(rel_path)
                print(f"📂 进入文件夹: {rel_path}")

            # 处理当前文件夹中的文件
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_file_path = os.path.relpath(file_path, folder_path)

                # 如果是 .py 文件且不以 __ 开头，则添加到处理列表
                if filename.endswith(".py"):
                    if not filename.startswith("__"):
                        py_files.append(file_path)
                        print(f"  ✅ 找到 Python 文件: {rel_file_path}")
                    else:
                        skipped_files.append(rel_file_path)
                        print(f"  ⏭️  跳过 (__ 开头): {rel_file_path}")
                else:
                    # 其他类型的文件，跳过
                    skipped_files.append(rel_file_path)
                    print(f"  ⏭️  跳过 (非 .py): {rel_file_path}")

        return py_files, skipped_files, processed_dirs

    @staticmethod
    def extract_repo_name_from_path(folder_path: str) -> Optional[str]:
        """
        从绝对路径中提取 cg- 开头的文件夹名作为仓库名

        Args:
            folder_path: 文件夹路径

        Returns:
            仓库名，如果没找到则返回None
        """
        path_parts = folder_path.split(os.sep)
        for part in path_parts:
            if part.startswith("cg-"):
                return part
        return None

    @staticmethod
    def create_backup_folder() -> str:
        """
        创建备份文件夹

        Returns:
            备份文件夹路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/sync_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    @staticmethod
    def backup_file(source_file: str, backup_dir: str) -> bool:
        """
        备份文件到指定目录

        Args:
            source_file: 源文件路径
            backup_dir: 备份目录

        Returns:
            是否成功
        """
        try:
            filename = os.path.basename(source_file)
            backup_path = os.path.join(backup_dir, filename)
            shutil.copy2(source_file, backup_path)
            return True
        except Exception as e:
            print(f"备份文件失败 {source_file}: {e}")
            return False

    @staticmethod
    def read_file_safely(file_path: str, encoding: str = "utf-8") -> Optional[str]:
        """
        安全读取文件内容

        Args:
            file_path: 文件路径
            encoding: 编码格式

        Returns:
            文件内容，失败返回None
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None

    @staticmethod
    def write_file_safely(
        file_path: str, content: str, encoding: str = "utf-8"
    ) -> bool:
        """
        安全写入文件内容

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式

        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """
        验证文件路径

        Args:
            file_path: 文件路径

        Returns:
            (是否有效, 错误信息)
        """
        if not file_path:
            return False, "文件路径不能为空"

        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"路径不是文件: {file_path}"

        return True, ""

    @staticmethod
    def validate_folder_path(folder_path: str) -> Tuple[bool, str]:
        """
        验证文件夹路径

        Args:
            folder_path: 文件夹路径

        Returns:
            (是否有效, 错误信息)
        """
        if not folder_path:
            return False, "文件夹路径不能为空"

        if not os.path.exists(folder_path):
            return False, f"文件夹不存在: {folder_path}"

        if not os.path.isdir(folder_path):
            return False, f"路径不是文件夹: {folder_path}"

        return True, ""

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            stat = os.stat(file_path)
            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "extension": os.path.splitext(file_path)[1].lower(),
            }
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return {}

    @staticmethod
    def ensure_directory_exists(dir_path: str) -> bool:
        """
        确保目录存在

        Args:
            dir_path: 目录路径

        Returns:
            是否成功
        """
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败 {dir_path}: {e}")
            return False

    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, "_")

        # 移除首尾空格和点
        filename = filename.strip(". ")

        # 确保不为空
        if not filename:
            filename = "unnamed"

        return filename
