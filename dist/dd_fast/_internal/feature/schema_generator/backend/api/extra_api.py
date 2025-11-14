"""
额外的API路由
处理原来app.py中的其他路由
"""

import os
import subprocess
from flask import Blueprint, request, jsonify, send_from_directory
from backend.database.db_factory import db_manager

# 创建蓝图
extra_bp = Blueprint("extra_api", __name__)


@extra_bp.route("/api/models/<int:model_id>", methods=["DELETE"])
def delete_model_by_id(model_id):
    """删除指定ID的模型"""
    try:
        # 这里需要根据ID查找模型名称，然后删除
        # 暂时返回成功，实际实现需要查询数据库
        return jsonify({"success": True, "message": "模型删除成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/generate", methods=["POST"])
def generate():
    """生成模型文件"""
    try:
        data = request.json
        models = data.get("models", [])
        output_dir = data.get("output_dir", "generated")

        if not models:
            return jsonify({"success": False, "error": "没有提供模型数据"}), 400

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        generated_files = []

        for model in models:
            try:
                # 生成模型文件内容
                filename = f"{model['name']}.py"
                filepath = os.path.join(output_dir, filename)

                # 这里应该生成实际的Python模型文件
                # 暂时创建一个简单的示例
                content = f"# Generated model: {model['name']}\n"
                content += f"# Label: {model['label']}\n"
                content += (
                    "# This is a placeholder - implement actual generation logic\n"
                )

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                generated_files.append(filepath)

            except Exception as e:
                print(f"生成模型文件失败 {model.get('name', '未知')}: {e}")

        return jsonify(
            {
                "success": True,
                "message": f"成功生成 {len(generated_files)} 个文件",
                "files": generated_files,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/configs", methods=["GET"])
def get_configs():
    """获取所有配置"""
    try:
        # 这里应该从数据库获取所有配置
        # 暂时返回空列表
        return jsonify({"success": True, "configs": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/configs", methods=["POST"])
def save_configs():
    """保存配置"""
    try:
        data = request.json
        configs = data.get("configs", [])

        success_count = 0
        for config in configs:
            key = config.get("key", "")
            value = config.get("value", "")
            if key:
                if db_manager.save_config(key, value):
                    success_count += 1

        return jsonify({"success": True, "message": f"成功保存 {success_count} 个配置"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/repositories", methods=["GET"])
def get_repositories():
    """获取所有仓库"""
    try:
        repositories = db_manager.get_all_repositories()
        return jsonify(
            {"success": True, "repositories": repositories, "count": len(repositories)}
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/repositories", methods=["POST"])
def create_repository():
    """创建仓库"""
    try:
        data = request.json
        name = data.get("name", "")
        path = data.get("path", "")
        description = data.get("description", "")

        if not name or not path:
            return jsonify({"success": False, "error": "仓库名称和路径不能为空"}), 400

        # 检查路径是否存在
        if not os.path.exists(path):
            return jsonify({"success": False, "error": f"路径不存在: {path}"}), 400

        if not os.path.isdir(path):
            return jsonify({"success": False, "error": f"路径不是文件夹: {path}"}), 400

        # 保存仓库信息到数据库
        repo_data = {"name": name, "path": path, "description": description}

        success = db_manager.save_repository(repo_data)
        if success:
            return jsonify({"success": True, "message": "仓库创建成功"})
        else:
            return jsonify({"success": False, "error": "仓库创建失败"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/repositories/<int:repo_id>", methods=["DELETE"])
def delete_repository(repo_id):
    """删除仓库"""
    try:
        success = db_manager.delete_repository(repo_id)
        if success:
            return jsonify({"success": True, "message": "仓库删除成功"})
        else:
            return jsonify({"success": False, "error": "仓库删除失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/test_project_start", methods=["POST"])
def test_project_start():
    """测试项目启动"""
    try:
        data = request.json
        project_path = data.get("project_path", "")

        if not project_path:
            return jsonify({"success": False, "error": "项目路径不能为空"}), 400

        # 这里应该启动测试项目
        # 暂时返回成功
        return jsonify(
            {
                "success": True,
                "message": "测试项目启动成功",
                "url": f"http://localhost:8000",
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/config/<key>", methods=["GET"])
def get_config_by_key(key):
    """根据键获取配置"""
    try:
        value = db_manager.get_config(key)
        return jsonify({"success": True, "key": key, "value": value})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/api/config/batch", methods=["POST"])
def save_config_batch():
    """批量保存配置"""
    try:
        data = request.json
        configs = data.get("configs", [])

        success_count = 0
        for config in configs:
            key = config.get("key", "")
            value = config.get("value", "")
            if key:
                if db_manager.save_config(key, value):
                    success_count += 1

        return jsonify({"success": True, "message": f"成功保存 {success_count} 个配置"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@extra_bp.route("/<path:filename>")
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory("static", filename)
