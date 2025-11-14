"""
MySQL数据库管理模块
处理所有MySQL数据库相关操作
"""

import pymysql
import json
from typing import List, Dict, Optional, Any
import os
from datetime import datetime


class MySQLManager:
    def __init__(self):
        self.connection_config = self._get_connection_config()
        self._initialized = False

    def _get_connection_config(self):
        """获取数据库连接配置"""
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 3306)),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "schema_generator"),
            "charset": "utf8mb4",
            "autocommit": True,
        }

    def _ensure_initialized(self):
        """确保数据库已初始化"""
        if not self._initialized:
            self.init_db()
            self._initialized = True

    def get_connection(self):
        """获取数据库连接"""
        self._ensure_initialized()
        try:
            return pymysql.connect(**self.connection_config)
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    def init_db(self):
        """初始化数据库和表结构"""
        try:
            # 先连接到MySQL服务器（不指定数据库）
            server_config = self.connection_config.copy()
            database_name = server_config.pop("database")

            conn = pymysql.connect(**server_config)
            cursor = conn.cursor()

            # 创建数据库（如果不存在）
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"USE `{database_name}`")

            # 创建所有表
            self._create_tables(cursor)

            conn.commit()
            conn.close()
            print(f"✅ MySQL数据库 '{database_name}' 初始化成功")

        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            raise

    def _create_tables(self, cursor):
        """创建所有表"""
        # 创建 models 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                label VARCHAR(255) NOT NULL,
                primary_key VARCHAR(255),
                entry VARCHAR(255) DEFAULT 'list',
                parent TEXT,
                action TEXT,
                fields TEXT,
                base_props TEXT,
                custom_actions TEXT,
                source_file VARCHAR(500),
                repo_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_repo_name (repo_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        )

        # 创建 repositories 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                path VARCHAR(500) NOT NULL UNIQUE,
                description TEXT,
                last_import_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_name (name),
                INDEX idx_path (path)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        )

        # 创建 link_forms 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS link_forms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                fields TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        )

        # 创建 inline_models 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inline_models (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                fields TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        )

        # 创建 configs 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                config_key VARCHAR(255) NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_key (config_key)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        )

    # ==================== 模型管理 ====================

    def save_model(self, model_data: Dict[str, Any]) -> bool:
        """保存模型到数据库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查模型是否已存在
            cursor.execute(
                "SELECT id FROM models WHERE name = %s", (model_data["name"],)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新现有模型
                cursor.execute(
                    """
                    UPDATE models SET 
                        label = %s, primary_key = %s, entry = %s, parent = %s, 
                        action = %s, fields = %s, base_props = %s, custom_actions = %s,
                        source_file = %s, repo_name = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE name = %s
                """,
                    (
                        model_data["label"],
                        model_data.get("primary_key", ""),
                        model_data.get("entry", "list"),
                        json.dumps(model_data.get("parent", "")),
                        json.dumps(model_data.get("action", [])),
                        json.dumps(model_data.get("fields", [])),
                        json.dumps(model_data.get("base_props", {})),
                        json.dumps(model_data.get("custom_actions", [])),
                        model_data.get("source_file", ""),
                        model_data.get("repo_name", ""),
                        model_data["name"],
                    ),
                )
            else:
                # 插入新模型
                cursor.execute(
                    """
                    INSERT INTO models (name, label, primary_key, entry, parent, action, fields, base_props, custom_actions, source_file, repo_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        model_data["name"],
                        model_data["label"],
                        model_data.get("primary_key", ""),
                        model_data.get("entry", "list"),
                        json.dumps(model_data.get("parent", "")),
                        json.dumps(model_data.get("action", [])),
                        json.dumps(model_data.get("fields", [])),
                        json.dumps(model_data.get("base_props", {})),
                        json.dumps(model_data.get("custom_actions", [])),
                        model_data.get("source_file", ""),
                        model_data.get("repo_name", ""),
                    ),
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存模型失败: {e}")
            return False

    def get_all_models(self) -> List[Dict[str, Any]]:
        """获取所有模型"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM models ORDER BY created_at DESC")
            rows = cursor.fetchall()

            models = []
            for row in rows:
                model = {
                    "id": row["id"],
                    "name": row["name"],
                    "label": row["label"],
                    "primary_key": row["primary_key"],
                    "entry": row["entry"],
                    "parent": json.loads(row["parent"]) if row["parent"] else "",
                    "action": json.loads(row["action"]) if row["action"] else [],
                    "fields": json.loads(row["fields"]) if row["fields"] else [],
                    "base_props": (
                        json.loads(row["base_props"]) if row["base_props"] else {}
                    ),
                    "custom_actions": (
                        json.loads(row["custom_actions"])
                        if row["custom_actions"]
                        else []
                    ),
                    "source_file": row["source_file"],
                    "repo_name": row["repo_name"],
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                    "updated_at": (
                        row["updated_at"].isoformat() if row["updated_at"] else None
                    ),
                }
                models.append(model)

            conn.close()
            return models
        except Exception as e:
            print(f"获取模型失败: {e}")
            return []

    def get_model_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取模型"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM models WHERE name = %s", (name,))
            row = cursor.fetchone()

            if row:
                model = {
                    "id": row["id"],
                    "name": row["name"],
                    "label": row["label"],
                    "primary_key": row["primary_key"],
                    "entry": row["entry"],
                    "parent": json.loads(row["parent"]) if row["parent"] else "",
                    "action": json.loads(row["action"]) if row["action"] else [],
                    "fields": json.loads(row["fields"]) if row["fields"] else [],
                    "base_props": (
                        json.loads(row["base_props"]) if row["base_props"] else {}
                    ),
                    "custom_actions": (
                        json.loads(row["custom_actions"])
                        if row["custom_actions"]
                        else []
                    ),
                    "source_file": row["source_file"],
                    "repo_name": row["repo_name"],
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                    "updated_at": (
                        row["updated_at"].isoformat() if row["updated_at"] else None
                    ),
                }
                conn.close()
                return model

            conn.close()
            return None
        except Exception as e:
            print(f"获取模型失败: {e}")
            return None

    def delete_model(self, name: str) -> bool:
        """删除模型"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM models WHERE name = %s", (name,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除模型失败: {e}")
            return False

    # ==================== 仓库管理 ====================

    def save_repository(self, repo_data: Dict[str, Any]) -> bool:
        """保存仓库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查仓库是否已存在（根据路径）
            cursor.execute(
                "SELECT id FROM repositories WHERE path = %s", (repo_data["path"],)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新现有仓库
                cursor.execute(
                    """
                    UPDATE repositories SET 
                        name = %s, description = %s, last_import_at = %s, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE path = %s
                """,
                    (
                        repo_data["name"],
                        repo_data.get("description", ""),
                        repo_data.get("last_import_at"),
                        repo_data["path"],
                    ),
                )
            else:
                # 插入新仓库
                cursor.execute(
                    """
                    INSERT INTO repositories (name, path, description, last_import_at)
                    VALUES (%s, %s, %s, %s)
                """,
                    (
                        repo_data["name"],
                        repo_data["path"],
                        repo_data.get("description", ""),
                        repo_data.get("last_import_at"),
                    ),
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存仓库失败: {e}")
            return False

    def get_all_repositories(self) -> List[Dict[str, Any]]:
        """获取所有仓库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM repositories ORDER BY created_at DESC")
            rows = cursor.fetchall()

            repositories = []
            for row in rows:
                repo = {
                    "id": row["id"],
                    "name": row["name"],
                    "path": row["path"],
                    "description": row["description"],
                    "last_import_at": (
                        row["last_import_at"].isoformat()
                        if row["last_import_at"]
                        else None
                    ),
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                    "updated_at": (
                        row["updated_at"].isoformat() if row["updated_at"] else None
                    ),
                }
                repositories.append(repo)

            conn.close()
            return repositories
        except Exception as e:
            print(f"获取仓库失败: {e}")
            return []

    def delete_repository(self, repo_id: int) -> bool:
        """删除仓库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM repositories WHERE id = %s", (repo_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除仓库失败: {e}")
            return False

    # ==================== 配置管理 ====================

    def save_config(self, key: str, value: str) -> bool:
        """保存配置"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO configs (config_key, config_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE 
                config_value = VALUES(config_value),
                updated_at = CURRENT_TIMESTAMP
            """,
                (key, value),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def get_config(self, key: str) -> Optional[str]:
        """获取配置"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT config_value FROM configs WHERE config_key = %s", (key,)
            )
            row = cursor.fetchone()

            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None

    # ==================== 其他功能 ====================

    def save_link_form(self, name: str, fields: List[Dict]) -> bool:
        """保存链接表单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO link_forms (name, fields)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE 
                fields = VALUES(fields)
            """,
                (name, json.dumps(fields)),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存链接表单失败: {e}")
            return False

    def get_link_forms(self) -> List[Dict[str, Any]]:
        """获取所有链接表单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM link_forms ORDER BY created_at DESC")
            rows = cursor.fetchall()

            forms = []
            for row in rows:
                form = {
                    "id": row["id"],
                    "name": row["name"],
                    "fields": json.loads(row["fields"]),
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                }
                forms.append(form)

            conn.close()
            return forms
        except Exception as e:
            print(f"获取链接表单失败: {e}")
            return []

    def save_inline_model(self, name: str, fields: List[Dict]) -> bool:
        """保存内联模型"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO inline_models (name, fields)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE 
                fields = VALUES(fields)
            """,
                (name, json.dumps(fields)),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存内联模型失败: {e}")
            return False

    def get_inline_models(self) -> List[Dict[str, Any]]:
        """获取所有内联模型"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM inline_models ORDER BY created_at DESC")
            rows = cursor.fetchall()

            models = []
            for row in rows:
                model = {
                    "id": row["id"],
                    "name": row["name"],
                    "fields": json.loads(row["fields"]),
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                }
                models.append(model)

            conn.close()
            return models
        except Exception as e:
            print(f"获取内联模型失败: {e}")
            return []


# MySQL管理器类，通过工厂模式创建实例
