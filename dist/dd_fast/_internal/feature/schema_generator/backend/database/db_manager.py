"""
数据库管理模块
处理所有数据库相关操作
"""

import sqlite3
import json
from typing import List, Dict, Optional, Any


class DatabaseManager:
    def __init__(self, db_path: str = "models.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建 models 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                primary_key TEXT,
                entry TEXT DEFAULT 'list',
                parent TEXT,
                action TEXT,
                fields TEXT,
                base_props TEXT,
                custom_actions TEXT,
                source_file TEXT,
                repo_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建 link_forms 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS link_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                fields TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建 inline_models 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS inline_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                fields TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建 configs 表（用于文件上传配置）
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # 创建 repositories 表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                description TEXT,
                last_import_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def save_model(self, model_data: Dict[str, Any]) -> bool:
        """保存模型到数据库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查模型是否已存在
            cursor.execute(
                "SELECT id FROM models WHERE name = ?", (model_data["name"],)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新现有模型
                cursor.execute(
                    """
                    UPDATE models SET 
                        label = ?, primary_key = ?, entry = ?, parent = ?, 
                        action = ?, fields = ?, base_props = ?, custom_actions = ?,
                        source_file = ?, repo_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
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
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM models ORDER BY created_at DESC")
            rows = cursor.fetchall()

            models = []
            for row in rows:
                model = {
                    "id": row[0],
                    "name": row[1],
                    "label": row[2],
                    "primary_key": row[3],
                    "entry": row[4],
                    "parent": json.loads(row[5]) if row[5] else "",
                    "action": json.loads(row[6]) if row[6] else [],
                    "fields": json.loads(row[7]) if row[7] else [],
                    "base_props": json.loads(row[8]) if row[8] else {},
                    "custom_actions": json.loads(row[9]) if row[9] else [],
                    "source_file": row[10],
                    "repo_name": row[11],
                    "created_at": row[12],
                    "updated_at": row[13],
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
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM models WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                model = {
                    "id": row[0],
                    "name": row[1],
                    "label": row[2],
                    "primary_key": row[3],
                    "entry": row[4],
                    "parent": json.loads(row[5]) if row[5] else "",
                    "action": json.loads(row[6]) if row[6] else [],
                    "fields": json.loads(row[7]) if row[7] else [],
                    "base_props": json.loads(row[8]) if row[8] else {},
                    "custom_actions": json.loads(row[9]) if row[9] else [],
                    "source_file": row[10],
                    "repo_name": row[11],
                    "created_at": row[12],
                    "updated_at": row[13],
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

            cursor.execute("DELETE FROM models WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除模型失败: {e}")
            return False

    def save_link_form(self, name: str, fields: List[Dict]) -> bool:
        """保存链接表单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO link_forms (name, fields)
                VALUES (?, ?)
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
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM link_forms ORDER BY created_at DESC")
            rows = cursor.fetchall()

            forms = []
            for row in rows:
                form = {
                    "id": row[0],
                    "name": row[1],
                    "fields": json.loads(row[2]),
                    "created_at": row[3],
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
                INSERT OR REPLACE INTO inline_models (name, fields)
                VALUES (?, ?)
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
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM inline_models ORDER BY created_at DESC")
            rows = cursor.fetchall()

            models = []
            for row in rows:
                model = {
                    "id": row[0],
                    "name": row[1],
                    "fields": json.loads(row[2]),
                    "created_at": row[3],
                }
                models.append(model)

            conn.close()
            return models
        except Exception as e:
            print(f"获取内联模型失败: {e}")
            return []

    def save_config(self, key: str, value: str) -> bool:
        """保存配置"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO configs (key, value)
                VALUES (?, ?)
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

            cursor.execute("SELECT value FROM configs WHERE key = ?", (key,))
            row = cursor.fetchone()

            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None

    # ==================== 仓库管理 ====================

    def save_repository(self, repo_data: Dict[str, Any]) -> bool:
        """保存仓库"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 检查仓库是否已存在（根据路径）
            cursor.execute(
                "SELECT id FROM repositories WHERE path = ?", (repo_data["path"],)
            )
            existing = cursor.fetchone()

            if existing:
                # 更新现有仓库
                cursor.execute(
                    """
                    UPDATE repositories SET 
                        name = ?, description = ?, last_import_at = ?
                    WHERE path = ?
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
                    VALUES (?, ?, ?, ?)
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
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM repositories ORDER BY created_at DESC")
            rows = cursor.fetchall()

            repositories = []
            for row in rows:
                repo = {
                    "id": row[0],
                    "name": row[1],
                    "path": row[2],
                    "description": row[3],
                    "last_import_at": row[4],
                    "created_at": row[5],
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

            cursor.execute("DELETE FROM repositories WHERE id = ?", (repo_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除仓库失败: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()
