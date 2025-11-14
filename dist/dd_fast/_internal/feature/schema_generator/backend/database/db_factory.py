"""
数据库工厂
根据配置选择使用MySQL或SQLite
"""

import os
from backend.database.mysql_manager import MySQLManager
from backend.database.db_manager import DatabaseManager


class DatabaseFactory:
    """数据库工厂类"""

    @staticmethod
    def create_manager():
        """创建数据库管理器"""
        # 检查是否配置了MySQL
        db_host = os.getenv("DB_HOST")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")

        if db_host and db_user:
            try:
                # 尝试使用MySQL
                print("🔍 尝试连接MySQL数据库...")
                mysql_manager = MySQLManager()
                # 测试连接
                mysql_manager._ensure_initialized()
                print("✅ MySQL数据库连接成功")
                return mysql_manager
            except Exception as e:
                print(f"⚠️  MySQL连接失败: {e}")
                print("🔄 回退到SQLite数据库...")

        # 使用SQLite作为默认数据库
        print("📁 使用SQLite数据库")
        sqlite_manager = DatabaseManager()
        print("✅ SQLite数据库初始化成功")
        return sqlite_manager


# 创建全局数据库管理器实例
db_manager = DatabaseFactory.create_manager()
