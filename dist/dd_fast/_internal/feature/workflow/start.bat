@echo off
chcp 65001 >nul
echo 🎯 Primer Workflow 可视化编辑器
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查必要文件
if not exist "workflow-visualizer.html" (
    echo ❌ 缺少文件: workflow-visualizer.html
    pause
    exit /b 1
)
if not exist "workflow-visualizer.js" (
    echo ❌ 缺少文件: workflow-visualizer.js
    pause
    exit /b 1
)
if not exist "demo.html" (
    echo ❌ 缺少文件: demo.html
    pause
    exit /b 1
)
if not exist "README.md" (
    echo ❌ 缺少文件: README.md
    pause
    exit /b 1
)

echo ✅ 所有必要文件检查通过
echo.

REM 启动服务器
python start.py %*
