#!/bin/bash

# Primer Workflow 可视化编辑器启动脚本 (Linux/Mac)

echo "🎯 Primer Workflow 可视化编辑器"
echo "========================================"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查必要文件
required_files=("workflow-visualizer.html" "workflow-visualizer.js" "demo.html" "README.md")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少文件: $file"
        exit 1
    fi
done

echo "✅ 所有必要文件检查通过"
echo ""

# 启动服务器
python3 start.py "$@"
