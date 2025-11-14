#!/usr/bin/env bash
set -euo pipefail

# macOS desktop app build using PyInstaller

APP_NAME="dd_fast"
ENTRY="app.py"

echo "🚀 开始构建 macOS 应用程序..."
echo "=================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 确保依赖
echo "📦 安装/更新依赖..."
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install --upgrade pyinstaller >/dev/null 2>&1

# 安装项目依赖
echo "📦 安装项目依赖..."
pip3 install rumps flask flask-cors pymysql >/dev/null 2>&1

# 清理之前的构建
echo "🧹 清理之前的构建..."
rm -rf build/ dist/ *.spec 2>/dev/null || true

# 构建 .app bundle
echo "🔨 开始构建应用程序..."
pyinstaller \
  --noconfirm \
  --windowed \
  --name "$APP_NAME" \
  --add-data "feature:feature" \
  --add-data "system:system" \
  --hidden-import "rumps" \
  --hidden-import "flask" \
  --hidden-import "flask_cors" \
  --hidden-import "pymysql" \
  --hidden-import "json" \
  --hidden-import "pathlib" \
  --hidden-import "typing" \
  --hidden-import "tkinter" \
  --hidden-import "threading" \
  --hidden-import "subprocess" \
  --hidden-import "webbrowser" \
  --onedir \
  "$ENTRY"

echo
echo "✅ 构建完成！"
echo "📱 应用程序位置: dist/$APP_NAME.app"
echo "💡 首次运行若提示「无法打开」，请在Finder中右键选择「打开」"
echo "🔧 或在「系统设置 -> 隐私与安全性」中允许运行"

