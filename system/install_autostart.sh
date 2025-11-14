#!/bin/bash
# dd_fast 自启动安装脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
DAEMON_SCRIPT="$PROJECT_ROOT/system/daemon.py"
PLIST_TEMPLATE="$PROJECT_ROOT/system/com.ddfast.plist"
PLIST_NAME="com.ddfast.daemon.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/$PLIST_NAME"
LOG_DIR="$HOME/Library/Logs/dd_fast"

echo "=========================================="
echo "dd_fast 自启动安装程序"
echo "=========================================="
echo ""

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3，请先安装 Python3${NC}"
    exit 1
fi

# 检查守护进程脚本
if [ ! -f "$DAEMON_SCRIPT" ]; then
    echo -e "${RED}错误: 守护进程脚本不存在: $DAEMON_SCRIPT${NC}"
    exit 1
fi

# 检查plist模板
if [ ! -f "$PLIST_TEMPLATE" ]; then
    echo -e "${RED}错误: plist模板不存在: $PLIST_TEMPLATE${NC}"
    exit 1
fi

# 获取Python3的实际路径
PYTHON3_PATH=$(which python3)
echo "Python3 路径: $PYTHON3_PATH"

# 创建日志目录
mkdir -p "$LOG_DIR"
echo "日志目录: $LOG_DIR"

# 创建LaunchAgents目录
mkdir -p "$LAUNCH_AGENTS_DIR"
echo "LaunchAgents 目录: $LAUNCH_AGENTS_DIR"

# 生成plist文件
echo ""
echo "正在生成 plist 文件..."
# 替换所有路径变量
sed "s|PYTHON3_PATH|$PYTHON3_PATH|g; s|DAEMON_SCRIPT_PATH|$DAEMON_SCRIPT|g; s|PROJECT_ROOT|$PROJECT_ROOT|g; s|LOG_DIR|$LOG_DIR|g" "$PLIST_TEMPLATE" > "$PLIST_FILE"

echo "plist 文件已生成: $PLIST_FILE"

# 如果已经加载了，先卸载
if launchctl list | grep -q "com.ddfast.daemon"; then
    echo ""
    echo -e "${YELLOW}检测到已安装的自启动服务，正在卸载...${NC}"
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    sleep 1
fi

# 加载服务
echo ""
echo "正在加载自启动服务..."
launchctl load "$PLIST_FILE"

# 等待一下
sleep 2

# 检查服务状态
if launchctl list | grep -q "com.ddfast.daemon"; then
    echo ""
    echo -e "${GREEN}✓ 自启动服务安装成功！${NC}"
    echo ""
    echo "服务信息:"
    echo "  - 服务名称: com.ddfast.daemon"
    echo "  - plist 文件: $PLIST_FILE"
    echo "  - 日志目录: $LOG_DIR"
    echo ""
    echo "管理命令:"
    echo "  启动服务: launchctl load $PLIST_FILE"
    echo "  停止服务: launchctl unload $PLIST_FILE"
    echo "  查看日志: tail -f $LOG_DIR/daemon.log"
    echo "  卸载服务: bash $SCRIPT_DIR/uninstall_autostart.sh"
    echo ""
    echo -e "${GREEN}程序将在下次登录时自动启动，并且会自动监控和重启！${NC}"
else
    echo ""
    echo -e "${RED}✗ 自启动服务加载失败${NC}"
    echo "请检查日志: $LOG_DIR/daemon.error.log"
    exit 1
fi

