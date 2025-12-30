#!/bin/bash
# dd_fast 部署脚本
# 用于在阿里云ECS上部署dd_fast服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="dd_fast"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="dd_fast"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PORT=5012

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}dd_fast 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
    echo "使用: sudo $0"
    exit 1
fi

# 1. 检查Python3
echo -e "${YELLOW}[1/7] 检查Python3...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python3${NC}"
    echo "Ubuntu/Debian: apt-get update && apt-get install -y python3 python3-pip python3-venv"
    echo "CentOS/RHEL: yum install -y python3 python3-pip"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ 找到Python: ${PYTHON_VERSION}${NC}"

# 检查venv模块是否可用
echo "检查venv模块..."
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}警告: venv模块不可用，尝试安装...${NC}"
    # 尝试安装python3-venv
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3-venv
    elif command -v yum &> /dev/null; then
        yum install -y python3-venv
    else
        echo -e "${RED}错误: 无法自动安装venv模块，请手动安装${NC}"
        echo "Ubuntu/Debian: apt-get install -y python3-venv"
        echo "CentOS/RHEL: yum install -y python3-venv"
        exit 1
    fi
fi
echo -e "${GREEN}✓ venv模块可用${NC}"

# 2. 创建安装目录
echo -e "${YELLOW}[2/7] 创建安装目录...${NC}"
mkdir -p ${INSTALL_DIR}
echo -e "${GREEN}✓ 安装目录: ${INSTALL_DIR}${NC}"

# 3. 复制项目文件
echo -e "${YELLOW}[3/7] 复制项目文件...${NC}"
# 假设当前目录是项目根目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

echo "从 ${PROJECT_ROOT} 复制文件到 ${INSTALL_DIR}..."
rsync -av --exclude='.git' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.idea' \
          --exclude='venv' \
          --exclude='*.log' \
          --exclude='logs' \
          ${PROJECT_ROOT}/ ${INSTALL_DIR}/
echo -e "${GREEN}✓ 文件复制完成${NC}"

# 4. 创建Python虚拟环境
echo -e "${YELLOW}[4/7] 创建Python虚拟环境...${NC}"
cd ${INSTALL_DIR} || exit 1
if [ -d "venv" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 虚拟环境创建失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
fi

# 检查虚拟环境是否存在
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}错误: 虚拟环境激活脚本不存在${NC}"
    echo "尝试重新创建虚拟环境..."
    rm -rf venv
    python3 -m venv venv
    if [ $? -ne 0 ] || [ ! -f "venv/bin/activate" ]; then
        echo -e "${RED}错误: 无法创建虚拟环境，请检查Python3和venv模块${NC}"
        exit 1
    fi
fi

# 5. 安装依赖
echo -e "${YELLOW}[5/7] 安装Python依赖...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: 无法激活虚拟环境${NC}"
    exit 1
fi
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ 依赖安装完成${NC}"
deactivate

# 6. 创建必要的目录
echo -e "${YELLOW}[6/7] 创建必要的目录...${NC}"
mkdir -p ${INSTALL_DIR}/logs
mkdir -p ${INSTALL_DIR}/feature/feishu/currency\ maintenance
mkdir -p ${INSTALL_DIR}/feature/feishu/update\ log
chmod 755 ${INSTALL_DIR}/logs
chmod 755 ${INSTALL_DIR}/feature/feishu/currency\ maintenance
chmod 755 ${INSTALL_DIR}/feature/feishu/update\ log
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 7. 安装systemd服务
echo -e "${YELLOW}[7/7] 安装systemd服务...${NC}"
# 复制服务文件
cp ${INSTALL_DIR}/deploy/${SERVICE_NAME}.service ${SERVICE_FILE}
# 替换服务文件中的路径（如果需要）
sed -i "s|/opt/dd_fast|${INSTALL_DIR}|g" ${SERVICE_FILE}

# 重新加载systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable ${SERVICE_NAME}

echo -e "${GREEN}✓ systemd服务安装完成${NC}"

# 8. 配置防火墙（如果使用firewalld）
if command -v firewall-cmd &> /dev/null; then
    echo -e "${YELLOW}[额外] 配置防火墙...${NC}"
    firewall-cmd --permanent --add-port=${PORT}/tcp
    firewall-cmd --reload
    echo -e "${GREEN}✓ 防火墙规则已添加（端口 ${PORT}）${NC}"
fi

# 9. 配置阿里云安全组提示
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}重要提示:${NC}"
echo -e "${YELLOW}1. 请在阿里云ECS控制台配置安全组规则，开放端口 ${PORT}${NC}"
echo -e "${YELLOW}2. 安全组规则: 入方向，TCP协议，端口 ${PORT}，授权对象 0.0.0.0/0${NC}"
echo -e "${YELLOW}========================================${NC}"

# 10. 启动服务
echo -e "${YELLOW}是否现在启动服务? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    systemctl start ${SERVICE_NAME}
    sleep 2
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        echo -e "${GREEN}✓ 服务启动成功${NC}"
        echo -e "${GREEN}服务状态:${NC}"
        systemctl status ${SERVICE_NAME} --no-pager -l
    else
        echo -e "${RED}✗ 服务启动失败，请检查日志:${NC}"
        echo "  journalctl -u ${SERVICE_NAME} -n 50"
    fi
else
    echo -e "${YELLOW}服务已安装但未启动，可以使用以下命令启动:${NC}"
    echo "  systemctl start ${SERVICE_NAME}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "常用命令:"
echo "  启动服务: systemctl start ${SERVICE_NAME}"
echo "  停止服务: systemctl stop ${SERVICE_NAME}"
echo "  重启服务: systemctl restart ${SERVICE_NAME}"
echo "  查看状态: systemctl status ${SERVICE_NAME}"
echo "  查看日志: journalctl -u ${SERVICE_NAME} -f"
echo "  查看应用日志: tail -f ${INSTALL_DIR}/logs/server.log"
echo ""
echo "服务地址:"
echo "  飞书Webhook: http://$(hostname -I | awk '{print $1}'):${PORT}/api/feishu-webhook"
echo "  健康检查: http://$(hostname -I | awk '{print $1}'):${PORT}/api/health"
echo "  Web界面: http://$(hostname -I | awk '{print $1}'):${PORT}/"

