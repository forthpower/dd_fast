"""
Schema Generator - 主应用文件
使用模块化结构重构后的版本
"""

from backend.api.extra_api import extra_bp

# 导入模块化组件
from backend.database.db_factory import db_manager
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from backend.api.model_api import model_bp

app = Flask(__name__, static_folder="static")
CORS(app)  # 允许跨域请求

# 注册蓝图
app.register_blueprint(model_bp)
app.register_blueprint(extra_bp)

# 初始化数据库
db_manager.init_db()


@app.route("/")
def index():
    """主页"""
    return send_from_directory("static", "index.html")


@app.route("/health")
def health():
    """健康检查"""
    return jsonify({"status": "ok", "message": "Schema Generator is running"})


@app.route("/api/config", methods=["GET"])
def get_config():
    """获取配置"""
    try:
        # 这里可以添加更多配置项
        config = {
            "version": "2.0.0",
            "features": {
                "batch_import": True,
                "auto_sync": True,
                "constant_detection": True,
            },
        }
        return jsonify({"success": True, "config": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config", methods=["POST"])
def save_config():
    """保存配置"""
    try:
        data = request.json
        key = data.get("key", "")
        value = data.get("value", "")

        if not key:
            return jsonify({"success": False, "error": "配置键不能为空"}), 400

        success = db_manager.save_config(key, value)
        if success:
            return jsonify({"success": True, "message": "配置保存成功"})
        else:
            return jsonify({"success": False, "error": "配置保存失败"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    import os
    import signal
    import sys
    
    # 处理Ctrl+C信号
    def signal_handler(sig, frame):
        print("\n🛑 正在停止服务器...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 启动 Schema Generator...")
    print("📁 使用模块化结构")
    print("🗄️  数据库已初始化")
    print("🌐 启动服务器...")
    print("💡 提示: 使用 Ctrl+C 停止服务器")

    try:
        app.run(debug=True, host="0.0.0.0", port=5010, use_reloader=True)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)
