from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sqlite3
import re
import ast
import os
import shutil
from datetime import datetime
import requests
import subprocess
import webbrowser
import time
import traceback

app = Flask(__name__, static_folder="static")
CORS(app)  # 允许跨域请求


# 数据库初始化
def init_db():
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS models
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       label
                       TEXT
                       NOT
                       NULL,
                       primary_key
                       TEXT,
                       entry
                       TEXT
                       DEFAULT
                       'list',
                       parent
                       TEXT,
                       action
                       TEXT,
                       fields
                       TEXT,
                       base_props
                       TEXT,
                       custom_actions
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 创建 link_forms 表
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS link_forms
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       fields
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 创建 inline_models 表
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS inline_models
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       fields
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 创建 configs 表（用于文件上传配置）
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS configs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       upload_type
                       TEXT
                       NOT
                       NULL,
                       config
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 创建 repositories 表（用于保存导入的仓库路径）
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS repositories
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       path
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       description
                       TEXT,
                       last_import_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 创建配置表
    cursor.execute(
        """
                   CREATE TABLE IF NOT EXISTS config
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       key
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       value
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   """
    )

    # 插入默认配置（如果不存在）
    default_configs = [
        (
            "project_path",
            "/Users/centurygame/PycharmProjects/cg-endpoint-demo",
            "项目路径",
        ),
        ("project_app", "app.py", "项目启动文件"),
        ("api_url", "http://10.0.49.158:5004/api/v1/admin/endpoints", "API 地址"),
        (
            "sync_url",
            "http://10.0.49.158:5004/api/v1/admin/endpoints/sync/demo",
            "同步地址",
        ),
        ("home_url", "http://localhost:8000/home/", "首页地址"),
        (
            "token",
            "eyJhbGciOiJIUzUxMiIsImlhdCI6MTc2MDAwOTA5OCwiZXhwIjoxNzYxODIzNDk4fQ.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InlvbmdqaWFuLmRhaSJ9.jxsAefu1Xmi63wr3o026HMuV5l_MFHdlDBbvik8Pa5WDOYt_ioViKUnaBx231ja6DS5K-Fi11Cjl8dddhYzQ1w",
            "认证 Token",
        ),
    ]

    for key, value, description in default_configs:
        cursor.execute(
            "INSERT OR IGNORE INTO config (key, value, description) VALUES (?, ?, ?)",
            (key, value, description),
        )

    conn.commit()
    conn.close()


# 初始化数据库
init_db()


@app.route("/")
def index():
    return app.send_static_file("index.html")  # 返回静态目录里的 index.html


# 获取所有模型
@app.route("/api/models", methods=["GET"])
def get_models():
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM models ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

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
            "created_at": row[10],
            "updated_at": row[11],
        }
        models.append(model)

    return jsonify(models)


# 保存模型
@app.route("/api/models", methods=["POST"])
def save_model():
    data = request.json

    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    # 检查模型名称是否已存在
    cursor.execute("SELECT id FROM models WHERE name = ?", (data.get("name"),))
    existing = cursor.fetchone()

    if existing:
        # 更新现有模型
        cursor.execute(
            """
                       UPDATE models
                       SET label          = ?,
                           primary_key    = ?,
                           entry          = ?,
                           parent         = ?,
                           action         = ?,
                           fields         = ?,
                           base_props     = ?,
                           custom_actions = ?,
                           updated_at     = CURRENT_TIMESTAMP
                       WHERE name = ?
                       """,
            (
                data.get("label"),
                data.get("primary_key", ""),
                data.get("entry", "list"),
                json.dumps(data.get("parent", "")),
                json.dumps(data.get("action", [])),
                json.dumps(data.get("fields", [])),
                json.dumps(data.get("base_props", {})),
                json.dumps(data.get("custom_actions", [])),
                data.get("name"),
            ),
        )
        model_id = existing[0]
    else:
        # 创建新模型
        cursor.execute(
            """
                       INSERT INTO models (name, label, primary_key, entry, parent, action, fields, base_props,
                                           custom_actions)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """,
            (
                data.get("name"),
                data.get("label"),
                data.get("primary_key", ""),
                data.get("entry", "list"),
                json.dumps(data.get("parent", "")),
                json.dumps(data.get("action", [])),
                json.dumps(data.get("fields", [])),
                json.dumps(data.get("base_props", {})),
                json.dumps(data.get("custom_actions", [])),
            ),
        )
        model_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({"success": True, "model_id": model_id})


# 删除模型
@app.route("/api/models/<int:model_id>", methods=["DELETE"])
def delete_model(model_id):
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json

    # 保存到数据库
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    # 检查模型名称是否已存在
    cursor.execute("SELECT id FROM models WHERE name = ?", (data.get("name"),))
    existing = cursor.fetchone()

    if existing:
        # 更新现有模型
        cursor.execute(
            """
                       UPDATE models
                       SET label          = ?,
                           primary_key    = ?,
                           entry          = ?,
                           parent         = ?,
                           action         = ?,
                           fields         = ?,
                           base_props     = ?,
                           custom_actions = ?,
                           updated_at     = CURRENT_TIMESTAMP
                       WHERE name = ?
                       """,
            (
                data.get("label"),
                data.get("primary_key", ""),
                data.get("entry", "list"),
                json.dumps(data.get("parent", "")),
                json.dumps(data.get("action", [])),
                json.dumps(data.get("fields", [])),
                json.dumps(data.get("base_props", {})),
                json.dumps(data.get("custom_actions", [])),
                data.get("name"),
            ),
        )
    else:
        # 创建新模型
        cursor.execute(
            """
                       INSERT INTO models (name, label, primary_key, entry, parent, action, fields, base_props,
                                           custom_actions)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                       """,
            (
                data.get("name"),
                data.get("label"),
                data.get("primary_key", ""),
                data.get("entry", "list"),
                json.dumps(data.get("parent", "")),
                json.dumps(data.get("action", [])),
                json.dumps(data.get("fields", [])),
                json.dumps(data.get("base_props", {})),
                json.dumps(data.get("custom_actions", [])),
            ),
        )

    conn.commit()
    conn.close()

    return jsonify(data)


# LinkForms API
@app.route("/api/link_forms", methods=["GET"])
def get_link_forms():
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM link_forms")
    rows = cursor.fetchall()
    conn.close()

    link_forms = []
    for row in rows:
        link_forms.append(
            {
                "id": row[0],
                "name": row[1],
                "fields": json.loads(row[2]),
                "created_at": row[3],
            }
        )

    return jsonify(link_forms)


@app.route("/api/link_forms", methods=["POST"])
def save_link_form():
    data = request.json
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM link_forms WHERE name = ?", (data.get("name"),))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
                       UPDATE link_forms
                       SET fields = ?
                       WHERE name = ?
                       """,
            (json.dumps(data.get("fields", [])), data.get("name")),
        )
    else:
        cursor.execute(
            """
                       INSERT INTO link_forms (name, fields)
                       VALUES (?, ?)
                       """,
            (data.get("name"), json.dumps(data.get("fields", []))),
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# InlineModels API
@app.route("/api/inline_models", methods=["GET"])
def get_inline_models():
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inline_models")
    rows = cursor.fetchall()
    conn.close()

    inline_models = []
    for row in rows:
        inline_models.append(
            {
                "id": row[0],
                "name": row[1],
                "fields": json.loads(row[2]),
                "created_at": row[3],
            }
        )

    return jsonify(inline_models)


@app.route("/api/inline_models", methods=["POST"])
def save_inline_model():
    data = request.json
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM inline_models WHERE name = ?", (data.get("name"),))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
                       UPDATE inline_models
                       SET fields = ?
                       WHERE name = ?
                       """,
            (json.dumps(data.get("fields", [])), data.get("name")),
        )
    else:
        cursor.execute(
            """
                       INSERT INTO inline_models (name, fields)
                       VALUES (?, ?)
                       """,
            (data.get("name"), json.dumps(data.get("fields", []))),
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# Configs API
@app.route("/api/configs", methods=["GET"])
def get_configs():
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configs")
    rows = cursor.fetchall()
    conn.close()

    configs = []
    for row in rows:
        configs.append(
            {
                "id": row[0],
                "name": row[1],
                "upload_type": row[2],
                "config": json.loads(row[3]),
                "created_at": row[4],
            }
        )

    return jsonify(configs)


@app.route("/api/configs", methods=["POST"])
def save_config():
    data = request.json
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM configs WHERE name = ?", (data.get("name"),))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
                       UPDATE configs
                       SET upload_type = ?,
                           config      = ?
                       WHERE name = ?
                       """,
            (
                data.get("upload_type"),
                json.dumps(data.get("config", {})),
                data.get("name"),
            ),
        )
    else:
        cursor.execute(
            """
                       INSERT INTO configs (name, upload_type, config)
                       VALUES (?, ?, ?)
                       """,
            (
                data.get("name"),
                data.get("upload_type"),
                json.dumps(data.get("config", {})),
            ),
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# Repositories API - 仓库管理
@app.route("/api/repositories", methods=["GET"])
def get_repositories():
    """获取所有已保存的仓库"""
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM repositories ORDER BY last_import_at DESC")
    rows = cursor.fetchall()
    conn.close()

    repositories = []
    for row in rows:
        repositories.append(
            {
                "id": row[0],
                "name": row[1],
                "path": row[2],
                "description": row[3],
                "last_import_at": row[4],
                "created_at": row[5],
            }
        )

    return jsonify(repositories)


@app.route("/api/repositories", methods=["POST"])
def save_repository():
    """保存仓库信息"""
    data = request.json
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()

    # 检查路径是否已存在
    cursor.execute("SELECT id FROM repositories WHERE path = ?", (data.get("path"),))
    existing = cursor.fetchone()

    if existing:
        # 更新最后导入时间
        cursor.execute(
            """
                       UPDATE repositories
                       SET name           = ?,
                           description    = ?,
                           last_import_at = CURRENT_TIMESTAMP
                       WHERE path = ?
                       """,
            (data.get("name"), data.get("description", ""), data.get("path")),
        )
    else:
        # 新增仓库
        cursor.execute(
            """
                       INSERT INTO repositories (name, path, description)
                       VALUES (?, ?, ?)
                       """,
            (data.get("name"), data.get("path"), data.get("description", "")),
        )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


@app.route("/api/repositories/<int:repo_id>", methods=["DELETE"])
def delete_repository(repo_id):
    """删除仓库"""
    conn = sqlite3.connect("models.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM repositories WHERE id = ?", (repo_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})


# 模型文件解析功能


def parse_model_file(content, file_type="auto"):
    """
    解析模型文件内容，支持多种格式：
    - Python SQLAlchemy Model（支持多个模型）
    - Django Model
    - SQL DDL
    - JSON Schema

    返回格式：
    - 单个模型：返回单个 schema 字典
    - 多个模型：返回包含多个 schema 的列表
    """

    # 类型映射字典
    type_mapping = {
        # Python/SQLAlchemy
        "Integer": "Integer",
        "String": "String",
        "Text": "TextArea",
        "Boolean": "Boolean",
        "DateTime": "DateTime",
        "Float": "Float",
        "Date": "DateTime",
        "Time": "String",
        "JSON": "Json",
        "BigInteger": "Integer",
        "SmallInteger": "Integer",
        "Numeric": "Float",
        "Decimal": "Float",
        # SQL
        "INT": "Integer",
        "INTEGER": "Integer",
        "BIGINT": "Integer",
        "SMALLINT": "Integer",
        "VARCHAR": "String",
        "CHAR": "String",
        "TEXT": "TextArea",
        "BOOLEAN": "Boolean",
        "BOOL": "Boolean",
        "DATETIME": "DateTime",
        "TIMESTAMP": "DateTime",
        "DATE": "DateTime",
        "FLOAT": "Float",
        "DOUBLE": "Float",
        "DECIMAL": "Float",
        "JSON": "Json",
        "BLOB": "File",
    }

    fields = []
    model_name = "imported_model"

    # 自动检测文件类型
    if "class" in content and ("db.Model" in content or "models.Model" in content):
        # Python Model (SQLAlchemy or Django)
        file_type = "python"
    elif "CREATE TABLE" in content.upper():
        # SQL DDL
        file_type = "sql"
    elif (
        content.strip().startswith("{")
        or "schema" in content
        and "=" in content
        and "{" in content
    ):
        # JSON 或 Python schema定义
        file_type = "json"

    if file_type == "python":
        # 解析 Python Model - 支持多个模型
        schemas = []

        # 找到所有的类定义
        class_pattern = r"class\s+(\w+)\s*\([^)]*(?:db\.Model|models\.Model)[^)]*\):\s*\n((?:(?!^class\s).*\n)*)"
        class_matches = re.finditer(class_pattern, content, re.MULTILINE)

        for class_match in class_matches:
            class_name = class_match.group(1)
            class_body = class_match.group(2)

            # 跳过 Mixin 类和工具类
            if "Mixin" in class_name or class_name in ["Tool"]:
                continue

            model_name = class_name.lower()
            model_fields = []

            # 提取 __tablename__
            tablename_match = re.search(
                r'__tablename__\s*=\s*[\'"](\w+)[\'"]', class_body
            )
            if tablename_match:
                model_name = tablename_match.group(1)

            # 提取字段定义
            field_patterns = [
                r"(\w+)\s*=\s*db\.Column\s*\((.*?)\)",
                r"(\w+)\s*=\s*models\.\w+Field\s*\((.*?)\)",
                r"(\w+)\s*=\s*Column\s*\((.*?)\)",
            ]

            for pattern in field_patterns:
                matches = re.finditer(pattern, class_body, re.MULTILINE)
                for match in matches:
                    field_name = match.group(1)
                    field_def = match.group(2)

                    # 跳过私有字段和特殊字段
                    if field_name.startswith("_") or field_name in [
                        "metadata",
                        "query",
                    ]:
                        continue

                    # 推断类型
                    field_type = "String"  # 默认类型
                    for py_type, schema_type in type_mapping.items():
                        if py_type in field_def:
                            field_type = schema_type
                            break

                    # 特殊处理 JSON 类型
                    if "JSON" in field_def or "Json" in field_def:
                        field_type = "Json"

                    # 提取字段标签
                    label_match = re.search(r'comment=[\'"]([^\'"]+)[\'"]', field_def)
                    label = (
                        label_match.group(1)
                        if label_match
                        else field_name.replace("_", " ").title()
                    )

                    # 检查是否必填
                    nullable_match = re.search(
                        r"nullable\s*=\s*(False|True)", field_def
                    )
                    is_required = nullable_match and nullable_match.group(1) == "False"

                    # 检查是否为主键
                    is_primary = (
                        "primary_key=True" in field_def
                        or "primary_key = True" in field_def
                    )

                    # 检查默认值
                    default_match = re.search(
                        r'default\s*=\s*[\'"]?([^\'",()\s]+)[\'"]?', field_def
                    )
                    default_value = default_match.group(1) if default_match else None

                    # 构建字段配置
                    field_config = {
                        "name": field_name,
                        "label": label,
                        "type": field_type,
                    }

                    # 添加验证器
                    if is_required and not is_primary:
                        field_config["validators"] = [{"name": "data_required"}]

                    # 主键设置为只读
                    if is_primary:
                        field_config["render_kw"] = {"readonly": True}

                    if default_value and default_value not in [
                        "None",
                        "null",
                        "datetime.now",
                        "datetime.utcnow",
                    ]:
                        field_config["default"] = default_value

                    model_fields.append(field_config)

            # 如果有字段，创建 schema
            if model_fields:
                # 查找主键字段
                primary_key = "id"
                for field in model_fields:
                    if field.get("render_kw", {}).get("readonly") and field["name"] in [
                        "id",
                        f"{model_name}_id",
                    ]:
                        primary_key = field["name"]
                        break

                schema = {
                    "name": model_name,
                    "label": class_name,
                    "primary_key": primary_key,
                    "entry": "list",
                    "parent": "",
                    "action": [
                        {"name": "list", "template": "tablebase"},
                        {"name": "create", "template": "formbase"},
                        {"name": "edit", "template": "editbase"},
                        {"name": "delete", "template": "button"},
                    ],
                    "fields": model_fields,
                    "base_props": {
                        "column_list": [f["name"] for f in model_fields[:6]],
                        "form_columns": [
                            f["name"]
                            for f in model_fields
                            if not f.get("render_kw", {}).get("readonly")
                        ],
                        "page_size": 20,
                    },
                    "custom_actions": [],
                }
                schemas.append(schema)

        # 如果找到多个模型，返回列表；否则返回单个或空
        if len(schemas) > 1:
            return schemas
        elif len(schemas) == 1:
            return schemas[0]
        # 如果没有找到任何模型，继续使用旧逻辑（向后兼容）

    if file_type == "sql":
        # 解析 SQL DDL
        # 提取表名
        table_match = re.search(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?",
            content,
            re.IGNORECASE,
        )
        if table_match:
            model_name = table_match.group(1).lower()

        # 提取字段定义
        # 匹配字段行
        field_pattern = r"`?(\w+)`?\s+([\w()]+)(?:\s+([^,\n]+))?"
        matches = re.finditer(field_pattern, content)

        for match in matches:
            field_name = match.group(1)
            sql_type = match.group(2).upper()
            constraints = match.group(3) or ""

            # 跳过 PRIMARY KEY, FOREIGN KEY 等约束
            if field_name.upper() in [
                "PRIMARY",
                "FOREIGN",
                "KEY",
                "INDEX",
                "CONSTRAINT",
                "UNIQUE",
            ]:
                continue

            # 推断类型
            field_type = "String"
            for sql_t, schema_type in type_mapping.items():
                if sql_type.startswith(sql_t):
                    field_type = schema_type
                    break

            # 检查是否必填
            is_required = "NOT NULL" in constraints.upper()

            # 检查默认值
            default_match = re.search(
                r'DEFAULT\s+[\'"]?([^\'",()\s]+)[\'"]?', constraints, re.IGNORECASE
            )
            default_value = default_match.group(1) if default_match else None

            # 检查注释
            comment_match = re.search(
                r'COMMENT\s+[\'"]([^\'"]+)[\'"]', constraints, re.IGNORECASE
            )
            label = comment_match.group(1) if comment_match else field_name

            # 构建字段配置
            field_config = {"name": field_name, "label": label, "type": field_type}

            if is_required:
                field_config["validators"] = [{"name": "data_required"}]

            if default_value and default_value.upper() not in [
                "NULL",
                "CURRENT_TIMESTAMP",
            ]:
                field_config["default"] = default_value

            fields.append(field_config)

    elif file_type == "json":
        # 解析 JSON Schema 或现有配置（支持Python格式的schema定义）
        data = None

        # 首先尝试用 JSON 解析
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试作为Python代码解析
            try:
                # 直接提取 schema = {...} 的内容，跳过前面的 import 语句
                schema_match = re.search(r"schema\s*=\s*(\{.*\})", content, re.DOTALL)
                if schema_match:
                    schema_str = schema_match.group(1)
                else:
                    # 如果没有找到 schema = {...}，尝试直接解析整个内容
                    schema_str = content

                # 移除Python注释（行尾的 # 注释）
                lines = schema_str.split("\n")
                cleaned_lines = []
                for line in lines:
                    # 检查是否在字符串内
                    in_string = False
                    quote_char = None
                    cleaned_line = []
                    i = 0
                    while i < len(line):
                        char = line[i]
                        # 处理字符串
                        if char in ['"', "'"]:
                            if not in_string:
                                in_string = True
                                quote_char = char
                            elif char == quote_char and (i == 0 or line[i - 1] != "\\"):
                                in_string = False
                                quote_char = None
                            cleaned_line.append(char)
                        # 处理注释
                        elif char == "#" and not in_string:
                            # 遇到注释，跳过剩余部分
                            break
                        else:
                            cleaned_line.append(char)
                        i += 1
                    cleaned_lines.append("".join(cleaned_line))

                schema_str = "\n".join(cleaned_lines)

                # 处理 copy_rule 的特殊格式
                # 1. {"开启"} -> 移除整行（使用默认行为）
                schema_str = re.sub(
                    r'"copy_rule":\s*\{\s*["\']开启["\']\s*\}\s*,?\s*\n?',
                    "",
                    schema_str,
                )
                # 2. {} 保持原样（可复制有按钮）
                # 3. "关闭" 保持原样（不可复制）

                # 清理不可打印字符
                schema_str = "".join(
                    char for char in schema_str if char.isprintable() or char in "\n\t"
                )

                # 查找并记录常量引用
                constants_found = []

                # 查找所有常量引用模式
                constant_patterns = [
                    r":\s*([A-Za-z_][A-Za-z0-9_]*\.[A-Z_][A-Z0-9_]*)\s*([,\}\]])",  # ClassName.ATTRIBUTE
                    r":\s*([A-Z_][A-Z0-9_]*)\s*([,\}\]])",  # CONSTANT_NAME
                ]

                def replace_and_record(match):
                    constant_ref = match.group(1)
                    if constant_ref not in constants_found:
                        constants_found.append(constant_ref)
                    return ": []" + match.group(2)

                # 替换常量引用为空列表并记录
                for pattern in constant_patterns:
                    schema_str = re.sub(pattern, replace_and_record, schema_str)

                # 使用 ast.literal_eval 解析
                data = ast.literal_eval(schema_str)

                # 标记常量引用
                if constants_found:
                    print(f"     🔍 发现常量引用: {', '.join(constants_found)}")
                    data["_has_constants"] = True
                    data["_constants_used"] = constants_found

                    # 在字段中标记常量引用
                    if "fields" in data and isinstance(data["fields"], list):
                        for field in data["fields"]:
                            if isinstance(field, dict):
                                field["_has_constants"] = True
                                field["_constant_refs"] = constants_found
            except (ValueError, SyntaxError) as e:
                print(f"Python parsing error: {e}")
                print(f"Content: {schema_str[:500]}")  # 打印前500个字符用于调试
                pass

        # 如果成功解析了数据
        if data and isinstance(data, dict):
            # 如果是完整的 schema
            if "name" in data and "fields" in data:
                return data
            # 如果是字段定义
            elif "properties" in data:
                # JSON Schema format
                model_name = data.get("title", "imported_model").lower()
                for field_name, field_def in data["properties"].items():
                    json_type = field_def.get("type", "string")
                    field_type = {
                        "string": "String",
                        "integer": "Integer",
                        "number": "Float",
                        "boolean": "Boolean",
                        "object": "Json",
                        "array": "Json",
                    }.get(json_type, "String")

                    fields.append(
                        {
                            "name": field_name,
                            "label": field_def.get("title", field_name),
                            "type": field_type,
                        }
                    )

    # 向后兼容：如果没有解析到字段，尝试简单的键值对
    if not fields and file_type not in ["python"]:  # Python 已经处理了多模型
        # 尝试解析简单的字段列表（一行一个字段名）
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("//"):
                # 简单的字段名
                field_name = re.sub(r"[^\w]", "", line)
                if field_name:
                    fields.append(
                        {
                            "name": field_name,
                            "label": field_name.replace("_", " ").title(),
                            "type": "String",
                        }
                    )

    # 构建完整的 schema（向后兼容单模型场景）
    if fields:
        schema = {
            "name": model_name,
            "label": model_name.replace("_", " ").title(),
            "primary_key": "id",
            "entry": "list",
            "parent": "",
            "action": [
                {"name": "list", "template": "tablebase"},
                {"name": "create", "template": "formbase"},
                {"name": "edit", "template": "editbase"},
                {"name": "delete", "template": "button"},
            ],
            "fields": fields,
            "base_props": {
                "column_list": [f["name"] for f in fields[:6]],  # 默认显示前6个字段
                "form_columns": [f["name"] for f in fields if f["name"] != "id"],
                "page_size": 20,
            },
            "custom_actions": [],
        }
        return schema

    # 如果什么都没解析到，返回空 schema
    return {
        "name": "imported_model",
        "label": "Imported Model",
        "primary_key": "id",
        "entry": "list",
        "parent": "",
        "action": [
            {"name": "list", "template": "tablebase"},
            {"name": "create", "template": "formbase"},
            {"name": "edit", "template": "editbase"},
            {"name": "delete", "template": "button"},
        ],
        "fields": [],
        "base_props": {"column_list": [], "form_columns": [], "page_size": 20},
        "custom_actions": [],
    }


@app.route("/api/parse_model", methods=["POST"])
def parse_model():
    """解析模型文件并返回 schema 配置（支持单个或多个模型）"""
    try:
        data = request.json
        content = data.get("content", "")
        file_type = data.get("file_type", "auto")

        result = parse_model_file(content, file_type)

        # 判断是单个模型还是多个模型
        is_multiple = isinstance(result, list)

        return jsonify(
            {
                "success": True,
                "schema": result if not is_multiple else None,  # 单个模型
                "schemas": result if is_multiple else None,  # 多个模型
                "is_multiple": is_multiple,
                "count": len(result) if is_multiple else 1,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/import_folder", methods=["POST"])
def import_folder():
    """
    批量导入文件夹中的所有 schema 文件

    请求格式：
    {
        "folder_path": "/path/to/schemas"
    }

    返回格式：
    {
        "success": True,
        "schemas": [...],  # 所有解析的schema列表
        "parent_menus": [...],  # 自动识别的父菜单列表
        "message": "成功导入 X 个文件"
    }
    """
    try:
        data = request.get_json()
        folder_path = data.get("folder_path", "").strip()

        if not folder_path:
            return jsonify({"success": False, "error": "请提供文件夹路径"}), 400

        # 检查文件夹是否存在
        if not os.path.exists(folder_path):
            return (
                jsonify({"success": False, "error": f"文件夹不存在: {folder_path}"}),
                400,
            )

        if not os.path.isdir(folder_path):
            return (
                jsonify({"success": False, "error": f"路径不是文件夹: {folder_path}"}),
                400,
            )

        # 从绝对路径中提取 cg- 开头的文件夹名作为仓库名
        repo_name = None
        path_parts = folder_path.split(os.sep)
        for part in path_parts:
            if part.startswith("cg-"):
                repo_name = part
                break

        print(f"\n{'='*60}")
        print(f"📦 开始扫描文件夹")
        print(f"   路径: {folder_path}")
        print(f"   仓库名: {repo_name or '未检测到'}")
        print(f"{'='*60}\n")

        # 递归扫描所有文件和文件夹
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

        print(f"\n{'='*60}")
        print(f"📊 扫描完成统计")
        print(f"   处理文件夹数: {len(processed_dirs) + 1}")  # +1 是根目录
        print(f"   找到 .py 文件: {len(py_files)}")
        print(f"   跳过的文件: {len(skipped_files)}")
        print(f"{'='*60}\n")

        if not py_files:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"文件夹中没有找到可处理的 .py 文件（已递归搜索所有子文件夹）\n扫描了 {len(processed_dirs) + 1} 个文件夹，跳过了 {len(skipped_files)} 个文件",
                    }
                ),
                400,
            )

        # 解析所有文件
        print(f"🔍 开始解析 {len(py_files)} 个 Python 文件\n")

        schemas = []
        parent_menus_dict = {}  # 使用字典去重
        failed_files = []

        for idx, file_path in enumerate(py_files, 1):
            rel_file_path = os.path.relpath(file_path, folder_path)
            print(f"[{idx}/{len(py_files)}] 解析: {rel_file_path}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 直接解析文件内容，跳过注释
                parsed = parse_model_file(content, "json")

                if parsed and "name" in parsed:
                    # 添加源文件路径信息，用于自动同步
                    parsed["source_file"] = file_path
                    # 添加仓库名信息
                    if repo_name:
                        parsed["repo_name"] = repo_name
                    if (
                        parsed["label"] == "imported_model"
                        or parsed["name"] == "imported_model"
                    ):
                        parsed["label"] = parsed["name"]
                    schemas.append(parsed)
                    print(
                        f"     ✅ 成功解析: {parsed.get('label', parsed.get('name', '未命名'))}"
                    )

                # 提取父菜单信息（对两种类型的解析结果都适用）
                if (
                    "parsed" in locals()
                    and parsed
                    and "parent" in parsed
                    and parsed["parent"]
                ):
                    parent_info = parsed["parent"]

                    # 如果 parent 是字符串，说明只有 label（内部标识符）
                    if isinstance(parent_info, str):
                        if parent_info and parent_info not in parent_menus_dict:
                            parent_menus_dict[parent_info] = {
                                "label": parent_info,  # label 是内部标识符
                                "name": parent_info.title(),  # name 是页面展示的字符串
                            }
                    # 如果 parent 是字典，包含 label 和 name
                    elif isinstance(parent_info, dict) and "label" in parent_info:
                        parent_label = parent_info["label"]
                        if parent_label and parent_label not in parent_menus_dict:
                            parent_menus_dict[parent_label] = {
                                "label": parent_label,  # label 是内部标识符
                                "name": parent_info.get(
                                    "name", parent_label.title()
                                ),  # name 是页面展示的字符串
                            }

            except Exception as e:
                print(f"     ❌ 解析错误: {str(e)}")
                failed_files.append(os.path.basename(file_path))

        # 转换父菜单字典为列表
        parent_menus = list(parent_menus_dict.values())

        # 打印最终统计
        print(f"\n{'='*60}")
        print(f"✨ 导入完成")
        print(f"   成功解析: {len(schemas)} 个模型")
        print(f"   父菜单: {len(parent_menus)} 个")
        print(f"   解析失败: {len(failed_files)} 个")
        print(f"{'='*60}\n")

        # 构建返回消息
        message = f"成功导入 {len(schemas)} 个模型"
        if repo_name:
            message = f"📦 {repo_name}: " + message
        if parent_menus:
            message += f"，自动识别 {len(parent_menus)} 个父菜单"
        if failed_files:
            message += f"\n\n解析失败的文件 ({len(failed_files)}): {', '.join(failed_files[:5])}"  # 只显示前5个
            if len(failed_files) > 5:
                message += f"... (还有 {len(failed_files) - 5} 个)"

        return jsonify(
            {
                "success": True,
                "schemas": schemas,
                "parent_menus": parent_menus,
                "repo_name": repo_name,  # 添加仓库名
                "message": message,
                "total_files": len(py_files),
                "success_count": len(schemas),
                "failed_count": len(failed_files),
                "failed_files": failed_files,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auto_sync", methods=["POST"])
def auto_sync():
    """
    自动同步功能 - 将生成的 schema 写回到源文件

    接收前端传来的 sync_data，包含：
    - file_path: 源文件路径
    - schema_content: 生成的 schema 内容
    - model_name: 模型名称

    返回格式：
    {
        "success": True,
        "success_count": 3,
        "failed_count": 0,
        "details": ["model1 同步成功", "model2 同步成功", ...]
    }
    """
    try:
        data = request.get_json()
        sync_data = data.get("sync_data", [])

        if not sync_data:
            return jsonify({"success": False, "error": "没有提供同步数据"}), 400

        # 创建备份文件夹（按时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = "backups"
        backup_dir = os.path.join(backup_root, f"sync_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"🚀 开始自动同步")
        print(f"   时间戳: {timestamp}")
        print(f"   备份目录: {backup_dir}")
        print(f"   同步模型数: {len(sync_data)}")
        print(f"{'='*60}\n")

        success_count = 0
        failed_count = 0
        details = []

        for item in sync_data:
            file_path = item.get("file_path")
            schema_content = item.get("schema_content")
            model_name = item.get("model_name", "Unknown")

            if not file_path or not schema_content:
                failed_count += 1
                details.append(f"❌ {model_name}: 缺少文件路径或内容")
                print(f"❌ {model_name}: 缺少文件路径或内容")
                continue

            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    failed_count += 1
                    details.append(f"❌ {model_name}: 文件不存在 ({file_path})")
                    print(f"❌ {model_name}: 文件不存在")
                    continue

                print(f"📝 同步 {model_name}...")

                # 备份原文件到独立文件夹
                filename = os.path.basename(file_path)
                backup_file_path = os.path.join(backup_dir, filename)
                shutil.copy2(file_path, backup_file_path)
                print(f"   ✅ 备份完成: {filename}")

                # 写入新的 schema 内容
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(schema_content)
                print(f"   ✅ 写入完成: {file_path}")

                success_count += 1
                details.append(f"✅ {model_name}: 同步成功")
                print(f"   ✅ 同步成功\n")

            except Exception as e:
                failed_count += 1
                details.append(f"❌ {model_name}: {str(e)}")
                print(f"   ❌ 同步失败: {str(e)}\n")

        # 本地同步总结
        print(f"{'='*60}")
        print(f"📊 本地同步完成")
        print(f"   ✅ 成功: {success_count} 个")
        print(f"   ❌ 失败: {failed_count} 个")
        print(f"   📁 备份: {backup_dir}")
        print(f"{'='*60}\n")

        # 集成远程同步功能（来自 sync.py）
        remote_sync_success = False
        remote_sync_message = ""

        # 从数据库获取配置
        remote_config = data.get("remote_sync", {})
        enabled = remote_config.get("enabled", True)  # 默认启用

        if enabled:
            try:
                # 从数据库读取配置
                config_conn = sqlite3.connect("models.db")
                config_cursor = config_conn.cursor()
                config_cursor.execute(
                    "SELECT key, value FROM config WHERE key IN (?, ?, ?, ?, ?, ?)",
                    (
                        "project_path",
                        "project_app",
                        "api_url",
                        "sync_url",
                        "home_url",
                        "token",
                    ),
                )
                config_rows = config_cursor.fetchall()
                config_conn.close()

                config_dict = {row[0]: row[1] for row in config_rows}

                # 获取配置（从数据库，如果不存在则使用默认值）
                project_path = config_dict.get(
                    "project_path",
                    "/Users/centurygame/PycharmProjects/cg-endpoint-demo",
                )
                project_app = config_dict.get("project_app", "app.py")
                api_url = config_dict.get(
                    "api_url", "http://10.0.49.158:5004/api/v1/admin/endpoints"
                )
                sync_url = config_dict.get(
                    "sync_url",
                    "http://10.0.49.158:5004/api/v1/admin/endpoints/sync/demo",
                )
                home_url = config_dict.get("home_url", "http://localhost:8000/home/")
                token = config_dict.get("token", "")

                headers = {"token": token} if token else {}

                # 第一步：启动项目（如果提供了项目路径）
                process = None
                if project_path and os.path.exists(project_path):
                    app_file = os.path.join(project_path, project_app)
                    if os.path.exists(app_file):
                        details.append(f"🚀 准备启动项目: {app_file}")

                        # 查找虚拟环境
                        venv_paths = [
                            (
                                ".venv",
                                os.path.join(project_path, ".venv", "bin", "activate"),
                            ),
                            (
                                "venv",
                                os.path.join(project_path, "venv", "bin", "activate"),
                            ),
                            (
                                "env",
                                os.path.join(project_path, "env", "bin", "activate"),
                            ),
                        ]

                        cmd = None
                        venv_used = "system python3"

                        for venv_name, activate_path in venv_paths:
                            if os.path.exists(activate_path):
                                # 使用 source 激活虚拟环境，然后执行 python3
                                cmd = f"source {activate_path} && python3 {project_app}"
                                venv_used = f"{venv_name}"
                                details.append(f"   找到虚拟环境: {venv_name}")
                                details.append(f"   激活脚本: {activate_path}")
                                break

                        if cmd is None:
                            # 没有虚拟环境，使用系统 Python
                            cmd = f"python3 {project_app}"
                            details.append(f"   未找到虚拟环境，使用系统 Python")

                        # 创建日志文件（使用绝对路径）
                        log_dir = os.path.join(
                            os.path.dirname(__file__), "backups", "logs"
                        )
                        os.makedirs(log_dir, exist_ok=True)
                        log_file = os.path.join(
                            log_dir, f"project_start_{timestamp}.log"
                        )

                        # 在命令中直接重定向输出，避免文件描述符问题（使用绝对路径）
                        cmd_with_redirect = f"{cmd} > {log_file} 2>&1 &"

                        details.append(f"   执行命令: {cmd}")
                        details.append(f"   工作目录: {project_path}")
                        details.append(f"   日志文件: {log_file}")

                        try:
                            # 不使用 nohup，而是直接后台运行，避免 Flask debug 模式的文件描述符问题
                            # 重定向 stdin 到 /dev/null 而不是关闭它
                            wrapper_cmd = f'bash -c "cd {project_path} && {cmd} > {log_file} 2>&1 </dev/null &"'
                            details.append(f"   完整启动命令: {wrapper_cmd}")

                            print(f"\n{'='*60}")
                            print(f"🚀 正在启动项目: {project_path}")
                            print(f"📝 执行命令: {cmd}")
                            print(f"📄 日志文件: {log_file}")
                            print(f"{'='*60}\n")

                            # 使用 shell 直接执行，不使用 start_new_session
                            # 这样可以保留文件描述符，让 Flask debug 模式正常工作
                            subprocess.Popen(
                                wrapper_cmd,
                                shell=True,
                                executable="/bin/bash",
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                close_fds=False,  # 不关闭文件描述符
                            )

                            # 等待让进程启动并实时读取日志
                            details.append(f"   等待项目启动...")
                            print("⏳ 等待项目启动...\n")
                            time.sleep(2)

                            # 实时读取并打印日志前50行
                            if os.path.exists(log_file):
                                try:
                                    with open(log_file, "r") as f:
                                        log_lines = f.readlines()
                                        if log_lines:
                                            print("📋 启动日志:")
                                            print("-" * 60)
                                            for i, line in enumerate(log_lines[:50]):
                                                print(line.rstrip())
                                            print("-" * 60)
                                            if len(log_lines) > 50:
                                                print(
                                                    f"... (还有 {len(log_lines) - 50} 行，查看完整日志: {log_file})"
                                                )
                                            print()
                                        else:
                                            print(
                                                "⚠️  日志文件为空，进程可能还在启动中\n"
                                            )
                                except Exception as e:
                                    print(f"⚠️  读取日志失败: {str(e)}\n")
                            else:
                                print(f"⚠️  日志文件尚未创建: {log_file}\n")

                            time.sleep(1)

                            # 查找启动的进程 - 更精确的匹配
                            find_process_cmd = f"ps aux | grep 'python3 {project_app}' | grep '{project_path}' | grep -v grep | awk '{{print $2}}'"
                            find_result = subprocess.run(
                                find_process_cmd,
                                shell=True,
                                capture_output=True,
                                text=True,
                            )

                            details.append(f"   查找进程命令: {find_process_cmd}")
                            details.append(
                                f"   查找结果: '{find_result.stdout.strip()}'"
                            )

                            print(f"🔍 查找进程...")
                            print(
                                f"   命令: ps aux | grep 'python3 {project_app}' | grep '{project_path}'"
                            )

                            if find_result.stdout.strip():
                                # 找到了进程
                                pid_str = find_result.stdout.strip()
                                details.append(f"⏱️  项目启动中... (PID: {pid_str})")
                                details.append(f"   使用虚拟环境: {venv_used}")
                                print(f"✅ 找到进程 PID: {pid_str}")
                                print(f"   使用虚拟环境: {venv_used}\n")
                                process = type(
                                    "obj",
                                    (object,),
                                    {"pid": int(pid_str), "poll": lambda: None},
                                )()
                            else:
                                details.append(f"❌ 未找到运行的进程")
                                details.append(f"   命令可能执行失败，请查看日志")
                                print(f"❌ 未找到运行的进程")
                                print(f"   命令可能执行失败\n")

                                # 尝试重新读取日志
                                try:
                                    time.sleep(1)
                                    if os.path.exists(log_file):
                                        with open(log_file, "r") as lf:
                                            log_content = lf.read()
                                            if log_content:
                                                details.append(f"   日志内容前20行:")
                                                print("📋 最新日志内容:")
                                                print("-" * 60)
                                                for line in log_content.split("\n")[
                                                    :20
                                                ]:
                                                    if line.strip():
                                                        details.append(f"     {line}")
                                                        print(line)
                                                print("-" * 60 + "\n")
                                    else:
                                        details.append(f"   日志文件不存在: {log_file}")
                                        print(f"⚠️  日志文件不存在: {log_file}\n")
                                except Exception as e:
                                    details.append(f"   读取日志失败: {str(e)}")
                                    print(f"⚠️  读取日志失败: {str(e)}\n")

                                process = None

                        except Exception as e:
                            details.append(f"❌ 启动命令执行失败: {str(e)}")
                            details.append(f"   命令: {cmd_with_redirect}")
                            raise

                        # 轮询检查项目是否启动成功
                        if process:
                            max_wait = 3
                            waited = 0
                            print(
                                f"🔄 轮询检查 API 是否可访问 (最多等待 {max_wait} 秒)...\n"
                            )

                            while waited < max_wait:
                                time.sleep(1)
                                waited += 1

                                # 检查进程是否还在运行
                                check_process_cmd = (
                                    f"ps -p {process.pid} > /dev/null 2>&1"
                                )
                                check_result = subprocess.run(
                                    check_process_cmd, shell=True
                                )

                                if check_result.returncode != 0:
                                    # 进程已退出，说明启动失败
                                    time.sleep(0.5)  # 等待日志写入完成

                                    details.append(f"❌ 项目启动失败 (进程已退出)")
                                    details.append(f"   日志文件: {log_file}")

                                    print(
                                        f"❌ 项目启动失败 (进程 {process.pid} 已退出)"
                                    )
                                    print(f"   日志文件: {log_file}\n")

                                    # 读取并显示错误日志的最后几行
                                    try:
                                        with open(log_file, "r") as f:
                                            log_lines = f.readlines()
                                            if log_lines:
                                                details.append(f"   最后 10 行日志:")
                                                print("📋 最后 10 行日志:")
                                                print("-" * 60)
                                                for line in log_lines[-10:]:
                                                    if line.strip():
                                                        details.append(
                                                            f"     {line.rstrip()}"
                                                        )
                                                        print(line.rstrip())
                                                print("-" * 60 + "\n")
                                    except Exception as e:
                                        details.append(f"   无法读取日志: {str(e)}")
                                        print(f"⚠️  无法读取日志: {str(e)}\n")
                                    break

                                # 尝试访问 API 验证启动
                                try:
                                    test_url = api_url.split("?")[0]
                                    print(
                                        f"   [{waited}/{max_wait}] 正在检查 API: {test_url}",
                                        end="",
                                        flush=True,
                                    )
                                    test_response = requests.get(
                                        test_url, headers=headers, timeout=2
                                    )
                                    if test_response.status_code in [200, 401, 403]:
                                        details.append(
                                            f"✅ 项目启动成功 (PID: {process.pid}, 耗时: {waited}秒)"
                                        )
                                        details.append(
                                            f"   API 响应码: {test_response.status_code}"
                                        )
                                        print(f" ✅")
                                        print(f"\n✅ 项目启动成功!")
                                        print(f"   PID: {process.pid}")
                                        print(f"   耗时: {waited} 秒")
                                        print(f"   API: {test_url}")
                                        print(
                                            f"   响应码: {test_response.status_code}\n"
                                        )
                                        break
                                    else:
                                        print(f" ⏳ (HTTP {test_response.status_code})")
                                except Exception as e:
                                    # 连接失败是正常的，继续等待
                                    print(f" ⏳ (等待中...)")
                                    if waited % 3 == 0:  # 每 3 秒输出一次状态
                                        details.append(
                                            f"   等待中... ({waited}/{max_wait}秒)"
                                        )
                            else:
                                # 超时
                                check_process_cmd = (
                                    f"ps -p {process.pid} > /dev/null 2>&1"
                                )
                                check_result = subprocess.run(
                                    check_process_cmd, shell=True
                                )

                                if check_result.returncode == 0:
                                    details.append(
                                        f"⚠️  项目启动超时，但进程仍在运行 (PID: {process.pid})"
                                    )
                                    details.append(
                                        f"   可能需要更长时间启动，请手动检查"
                                    )
                                    details.append(f"   日志文件: {log_file}")

                                    print(f"\n⚠️  项目启动超时，但进程仍在运行")
                                    print(f"   PID: {process.pid}")
                                    print(f"   可能需要更长时间启动，请手动检查")
                                    print(f"   日志文件: {log_file}\n")
                                else:
                                    details.append(f"❌ 项目启动超时且进程已退出")
                                    details.append(f"   日志文件: {log_file}")

                                    print(f"\n❌ 项目启动超时且进程已退出")
                                    print(f"   日志文件: {log_file}\n")

                                    # 读取日志
                                    try:
                                        with open(log_file, "r") as f:
                                            log_lines = f.readlines()
                                            if log_lines:
                                                details.append(f"   最后 10 行日志:")
                                                print("📋 最后 10 行日志:")
                                                print("-" * 60)
                                                for line in log_lines[-10:]:
                                                    if line.strip():
                                                        details.append(
                                                            f"     {line.rstrip()}"
                                                        )
                                                        print(line.rstrip())
                                                print("-" * 60 + "\n")
                                    except:
                                        pass
                    else:
                        details.append(f"⚠️  项目文件不存在: {app_file}")

                # 第二步：同步 schema
                if sync_url:
                    print(f"{'='*60}")
                    print(f"🔄 正在同步 Schema 到远程...")
                    print(f"   URL: {sync_url}")
                    print(f"{'='*60}\n")

                    time.sleep(1)
                    response = requests.get(sync_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    details.append("✅ 远程同步: Schema 同步成功")
                    remote_sync_success = True
                    remote_sync_message = "远程同步成功"

                    print(f"✅ Schema 同步成功!")
                    print(f"   响应码: {response.status_code}\n")

                    # 同步成功后等待3秒，确保远程服务器处理完成
                    details.append("⏱️  等待远程服务器处理...")
                    details.append("✅ 远程处理完成")

                # 第三步：打开浏览器（只在远程同步成功后）
                if home_url and remote_sync_success:
                    print(f"{'='*60}")
                    print(f"🌐 正在打开浏览器...")
                    print(f"   URL: {home_url}")
                    print(f"{'='*60}\n")

                    webbrowser.open(home_url)
                    details.append(f"🌐 已打开浏览器: {home_url}")

                    print(f"✅ 浏览器已打开\n")

            except Exception as e:
                details.append(f"⚠️  远程同步失败: {str(e)}")
                remote_sync_message = f"远程同步失败: {str(e)}"

                print(f"\n❌ 远程同步失败!")
                print(f"   错误: {str(e)}")
                print(f"{'='*60}\n")

        # 构建返回消息
        message = f"同步完成: 成功 {success_count} 个，失败 {failed_count} 个\n备份位置: {backup_dir}"
        if remote_sync_message:
            message += f"\n{remote_sync_message}"

        return jsonify(
            {
                "success": True,
                "success_count": success_count,
                "failed_count": failed_count,
                "details": details,
                "backup_dir": backup_dir,
                "remote_sync": remote_sync_success,
                "message": message,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test_project_start", methods=["POST"])
def test_project_start():
    """
    测试项目启动 - 调试用接口
    """
    try:
        data = request.get_json()
        project_path = data.get(
            "project_path", "/Users/centurygame/PycharmProjects/cg-endpoint-demo"
        )
        project_app = data.get("project_app", "app.py")

        details = []

        # 检查项目路径
        if not os.path.exists(project_path):
            return (
                jsonify({"success": False, "error": f"项目路径不存在: {project_path}"}),
                400,
            )

        app_file = os.path.join(project_path, project_app)
        if not os.path.exists(app_file):
            return (
                jsonify({"success": False, "error": f"项目文件不存在: {app_file}"}),
                400,
            )

        details.append(f"✅ 项目路径: {project_path}")
        details.append(f"✅ 项目文件: {app_file}")

        # 查找虚拟环境
        venv_paths = [
            (".venv", os.path.join(project_path, ".venv", "bin", "activate")),
            ("venv", os.path.join(project_path, "venv", "bin", "activate")),
            ("env", os.path.join(project_path, "env", "bin", "activate")),
        ]

        cmd = None
        venv_found = False

        for venv_name, activate_path in venv_paths:
            if os.path.exists(activate_path):
                # 使用 source 激活虚拟环境，然后执行 python3
                cmd = f"source {activate_path} && python3 {project_app}"
                details.append(f"✅ 找到虚拟环境: {venv_name}")
                details.append(f"   激活脚本: {activate_path}")
                venv_found = True
                break

        if not venv_found:
            cmd = f"python3 {project_app}"
            details.append(f"⚠️  未找到虚拟环境，将使用系统 Python")

        # 测试 Python 版本
        try:
            # 使用相同的环境测试 Python 版本
            if venv_found:
                test_cmd = f"source {activate_path} && python3 --version"
            else:
                test_cmd = "python3 --version"

            version_result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                shell=True,
                executable="/bin/bash",
                timeout=5,
            )
            python_version = (
                version_result.stdout.strip() or version_result.stderr.strip()
            )
            details.append(f"✅ Python 版本: {python_version}")
        except Exception as e:
            details.append(f"⚠️  无法获取 Python 版本: {str(e)}")

        # 创建测试日志（使用绝对路径）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(os.path.dirname(__file__), "backups", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"test_start_{timestamp}.log")

        details.append(f"📝 启动命令: {cmd}")
        details.append(f"📂 工作目录: {project_path}")
        details.append(f"📄 日志文件: {log_file}")

        # 启动项目 - 避免使用 nohup，防止 Flask debug 模式的文件描述符问题
        try:
            wrapper_cmd = (
                f'bash -c "cd {project_path} && {cmd} > {log_file} 2>&1 </dev/null &"'
            )
            details.append(f"📝 完整启动命令: {wrapper_cmd}")

            subprocess.Popen(
                wrapper_cmd,
                shell=True,
                executable="/bin/bash",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                close_fds=False,
            )

            # 等待一下让进程启动
            time.sleep(2)

            # 查找启动的进程
            find_process_cmd = f"ps aux | grep '[p]ython3 {project_app}' | grep '{project_path}' | grep -v grep"
            find_result = subprocess.run(
                find_process_cmd, shell=True, capture_output=True, text=True
            )

            if find_result.stdout.strip():
                # 找到了进程
                pid_line = find_result.stdout.strip().split()[1]
                details.append(f"🚀 项目已启动 (PID: {pid_line})")

                # 等待 5 秒检查状态
                time.sleep(5)

                # 再次检查进程是否还在
                check_result = subprocess.run(
                    f"ps -p {pid_line} > /dev/null 2>&1", shell=True
                )

                if check_result.returncode != 0:
                    # 进程已退出
                    details.append(f"❌ 项目启动失败 (进程已退出)")
                    # 读取日志
                    try:
                        with open(log_file, "r") as f:
                            log_content = f.read()
                            details.append(f"📋 日志内容:")
                            for line in log_content.split("\n")[-15:]:
                                if line.strip():
                                    details.append(f"   {line}")
                    except Exception as e:
                        details.append(f"   无法读取日志: {str(e)}")

                    return jsonify(
                        {"success": False, "details": details, "log_file": log_file}
                    )
                else:
                    details.append(f"✅ 项目进程运行中")
                    details.append(f"💡 请手动检查 API 是否可访问")
                    details.append(f"💡 日志: {log_file}")

                    return jsonify(
                        {
                            "success": True,
                            "pid": int(pid_line),
                            "details": details,
                            "log_file": log_file,
                        }
                    )
            else:
                details.append(f"❌ 未找到运行的进程")
                details.append(f"   命令可能执行失败，请查看日志")

                # 读取日志
                try:
                    time.sleep(1)
                    with open(log_file, "r") as f:
                        log_content = f.read()
                        if log_content:
                            details.append(f"📋 日志内容:")
                            for line in log_content.split("\n")[-15:]:
                                if line.strip():
                                    details.append(f"   {line}")
                except:
                    pass

                return jsonify(
                    {"success": False, "details": details, "log_file": log_file}
                )

        except Exception as e:
            details.append(f"❌ 启动命令执行失败: {str(e)}")
            return jsonify({"success": False, "details": details, "error": str(e)})

    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": str(e), "traceback": traceback.format_exc()}
            ),
            500,
        )


# ==================== 配置管理 API ====================


@app.route("/api/config", methods=["GET"])
def get_config():
    """获取所有配置"""
    try:
        conn = sqlite3.connect("models.db")
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, description FROM config")
        rows = cursor.fetchall()
        conn.close()

        config = {}
        for key, value, description in rows:
            config[key] = {"value": value, "description": description}

        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/<key>", methods=["GET"])
def get_config_by_key(key):
    """获取单个配置"""
    try:
        conn = sqlite3.connect("models.db")
        cursor = conn.cursor()
        cursor.execute("SELECT value, description FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return jsonify({"key": key, "value": row[0], "description": row[1]})
        else:
            return jsonify({"error": "配置不存在"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["POST"])
def update_config():
    """更新配置"""
    try:
        data = request.json
        key = data.get("key")
        value = data.get("value")
        description = data.get("description", "")

        if not key or value is None:
            return jsonify({"error": "缺少必要参数"}), 400

        conn = sqlite3.connect("models.db")
        cursor = conn.cursor()

        # 使用 INSERT OR REPLACE 更新配置
        cursor.execute(
            """
            INSERT OR REPLACE INTO config (key, value, description, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
            (key, value, description),
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"配置 {key} 已更新"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config/batch", methods=["POST"])
def update_config_batch():
    """批量更新配置"""
    try:
        configs = request.json

        if not isinstance(configs, dict):
            return jsonify({"error": "参数格式错误"}), 400

        conn = sqlite3.connect("models.db")
        cursor = conn.cursor()

        for key, value in configs.items():
            cursor.execute(
                """
                INSERT OR REPLACE INTO config (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
                (key, value),
            )

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"已更新 {len(configs)} 个配置"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 显式提供静态文件（CSS、JS 等）
@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    print(app.url_map)
    # 禁用 reloader 避免进程不退出的问题
    # 如果需要自动重载功能，可以改为 use_reloader=True，但需要手动杀进程
    app.run(host="0.0.0.0", port=5010, debug=True, use_reloader=False)
