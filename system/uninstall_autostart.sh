#!/bin/bash
# dd_fast 自启动卸载脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_NAME="com.ddfast.daemon.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/$PLIST_NAME"

echo "=========================================="
echo "dd_fast 自启动卸载程序"
echo "=========================================="
echo ""

# 检查服务是否存在
if [ ! -f "$PLIST_FILE" ]; then
    echo -e "${YELLOW}未找到自启动服务，可能已经卸载${NC}"
    exit 0
fi

# 如果服务正在运行，先停止
if launchctl list | grep -q "com.ddfast.daemon"; then
    echo "正在停止服务..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ 服务已停止${NC}"
else
    echo -e "${YELLOW}服务未运行${NC}"
fi

# 删除plist文件
if [ -f "$PLIST_FILE" ]; then
    rm "$PLIST_FILE"
    echo -e "${GREEN}✓ plist 文件已删除${NC}"
fi

echo ""
echo -e "${GREEN}✓ 自启动服务已完全卸载${NC}"
echo ""
echo "注意: 日志文件仍保留在 ~/Library/Logs/dd_fast/ 目录中"
echo "如需删除日志，请手动删除该目录"

