#!/bin/bash
# 测试守护进程脚本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DAEMON_SCRIPT="$SCRIPT_DIR/daemon.py"

echo "=========================================="
echo "测试守护进程"
echo "=========================================="
echo ""

# 检查守护进程脚本
if [ ! -f "$DAEMON_SCRIPT" ]; then
    echo "错误: 守护进程脚本不存在: $DAEMON_SCRIPT"
    exit 1
fi

# 运行守护进程（前台运行，用于测试）
echo "启动守护进程（前台运行，按 Ctrl+C 停止）..."
echo ""
python3 "$DAEMON_SCRIPT"

