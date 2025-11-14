"""
模型相关API路由
处理模型CRUD操作、导入导出等功能
"""

import os
import json
from flask import Blueprint, request, jsonify
from backend.database.db_factory import db_manager
from backend.parser.model_parser import model_parser
from backend.utils.file_utils import FileUtils

# 创建蓝图
model_bp = Blueprint("model_api", __name__)


@model_bp.route("/api/models", methods=["GET"])
def get_all_models():
    """获取所有模型"""
    try:
        models = db_manager.get_all_models()
        return jsonify({"success": True, "models": models, "count": len(models)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/models/<model_name>", methods=["GET"])
def get_model(model_name):
    """获取指定模型"""
    try:
        model = db_manager.get_model_by_name(model_name)
        if model:
            return jsonify({"success": True, "model": model})
        else:
            return jsonify({"success": False, "error": "模型不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/models", methods=["POST"])
def create_model():
    """创建新模型"""
    try:
        data = request.json
        model_data = data.get("model", {})

        if not model_data.get("name"):
            return jsonify({"success": False, "error": "模型名称不能为空"}), 400

        success = db_manager.save_model(model_data)
        if success:
            return jsonify({"success": True, "message": "模型创建成功"})
        else:
            return jsonify({"success": False, "error": "模型创建失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/models/<model_name>", methods=["PUT"])
def update_model(model_name):
    """更新模型"""
    try:
        data = request.json
        model_data = data.get("model", {})
        model_data["name"] = model_name  # 确保名称一致

        success = db_manager.save_model(model_data)
        if success:
            return jsonify({"success": True, "message": "模型更新成功"})
        else:
            return jsonify({"success": False, "error": "模型更新失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/models/<model_name>", methods=["DELETE"])
def delete_model(model_name):
    """删除模型"""
    try:
        success = db_manager.delete_model(model_name)
        if success:
            return jsonify({"success": True, "message": "模型删除成功"})
        else:
            return jsonify({"success": False, "error": "模型删除失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/parse_model", methods=["POST"])
def parse_model():
    """解析模型文件并返回 schema 配置（支持单个或多个模型）"""
    try:
        data = request.json
        content = data.get("content", "")
        file_type = data.get("file_type", "auto")

        result = model_parser.parse_model_file(content, file_type)

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


@model_bp.route("/api/import_folder", methods=["POST"])
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

        # 验证文件夹路径
        is_valid, error_msg = FileUtils.validate_folder_path(folder_path)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400

        # 从绝对路径中提取 cg- 开头的文件夹名作为仓库名
        repo_name = FileUtils.extract_repo_name_from_path(folder_path)

        print(f"\n{'='*60}")
        print(f"📦 开始扫描文件夹")
        print(f"   路径: {folder_path}")
        print(f"   仓库名: {repo_name or '未检测到'}")
        print(f"{'='*60}\n")

        # 递归扫描所有文件和文件夹
        py_files, skipped_files, processed_dirs = FileUtils.scan_folder_recursively(
            folder_path
        )

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
                content = FileUtils.read_file_safely(file_path)
                if content is None:
                    failed_files.append(os.path.basename(file_path))
                    continue

                # 解析文件内容
                parsed = model_parser.parse_model_file(content, "json")

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

                # 提取父菜单信息
                if parsed and "parent" in parsed and parsed["parent"]:
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

        # 转换为列表
        parent_menus = list(parent_menus_dict.values())

        print(f"\n{'='*60}")
        print(f"📋 解析完成统计")
        print(f"   成功解析: {len(schemas)} 个文件")
        print(f"   失败文件: {len(failed_files)} 个")
        print(f"   识别父菜单: {len(parent_menus)} 个")
        if failed_files:
            print(f"   失败列表: {', '.join(failed_files)}")
        print(f"{'='*60}\n")

        return jsonify(
            {
                "success": True,
                "schemas": schemas,
                "parent_menus": parent_menus,
                "message": f"成功导入 {len(schemas)} 个文件，识别到 {len(parent_menus)} 个父菜单",
                "stats": {
                    "total_files": len(py_files),
                    "success_files": len(schemas),
                    "failed_files": len(failed_files),
                    "parent_menus": len(parent_menus),
                    "processed_dirs": len(processed_dirs) + 1,
                    "skipped_files": len(skipped_files),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/auto_sync", methods=["POST"])
def auto_sync():
    """自动同步模型文件"""
    try:
        data = request.get_json()
        models_to_sync = data.get("models", [])

        if not models_to_sync:
            return jsonify({"success": False, "error": "没有需要同步的模型"}), 400

        synced_count = 0
        failed_models = []

        for model_data in models_to_sync:
            try:
                # 保存模型到数据库
                success = db_manager.save_model(model_data)
                if success:
                    synced_count += 1
                else:
                    failed_models.append(model_data.get("name", "未知"))
            except Exception as e:
                failed_models.append(model_data.get("name", "未知"))
                print(f"同步模型失败 {model_data.get('name', '未知')}: {e}")

        return jsonify(
            {
                "success": True,
                "synced_count": synced_count,
                "failed_models": failed_models,
                "message": f"成功同步 {synced_count} 个模型",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/link_forms", methods=["GET"])
def get_link_forms():
    """获取所有链接表单"""
    try:
        forms = db_manager.get_link_forms()
        return jsonify({"success": True, "forms": forms, "count": len(forms)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/link_forms", methods=["POST"])
def save_link_form():
    """保存链接表单"""
    try:
        data = request.json
        name = data.get("name", "")
        fields = data.get("fields", [])

        if not name:
            return jsonify({"success": False, "error": "表单名称不能为空"}), 400

        success = db_manager.save_link_form(name, fields)
        if success:
            return jsonify({"success": True, "message": "链接表单保存成功"})
        else:
            return jsonify({"success": False, "error": "链接表单保存失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/inline_models", methods=["GET"])
def get_inline_models():
    """获取所有内联模型"""
    try:
        models = db_manager.get_inline_models()
        return jsonify({"success": True, "models": models, "count": len(models)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@model_bp.route("/api/inline_models", methods=["POST"])
def save_inline_model():
    """保存内联模型"""
    try:
        data = request.json
        name = data.get("name", "")
        fields = data.get("fields", [])

        if not name:
            return jsonify({"success": False, "error": "模型名称不能为空"}), 400

        success = db_manager.save_inline_model(name, fields)
        if success:
            return jsonify({"success": True, "message": "内联模型保存成功"})
        else:
            return jsonify({"success": False, "error": "内联模型保存失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
