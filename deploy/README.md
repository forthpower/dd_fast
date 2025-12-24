# dd_fast 阿里云ECS部署指南

本指南将帮助您将dd_fast项目部署到阿里云ECS服务器上。

## 前置要求

1. **阿里云ECS实例**
   - 操作系统: Ubuntu 20.04/22.04 或 CentOS 7/8
   - 最低配置: 1核2GB内存
   - 已配置SSH访问

2. **网络配置**
   - 确保ECS实例有公网IP或已配置弹性公网IP
   - 需要在安全组中开放端口5012

## 部署步骤

### 方法一：使用自动部署脚本（推荐）

1. **上传项目文件到服务器**
   ```bash
   # 在本地项目目录执行
   scp -r . root@your-server-ip:/tmp/dd_fast
   ```

2. **SSH登录到服务器**
   ```bash
   ssh root@your-server-ip
   ```

3. **运行部署脚本**
   ```bash
   cd /tmp/dd_fast
   chmod +x deploy/deploy.sh
   sudo ./deploy/deploy.sh
   ```

4. **配置阿里云安全组**
   - 登录阿里云控制台
   - 进入ECS实例 -> 安全组 -> 配置规则
   - 添加入方向规则：
     - 协议类型: TCP
     - 端口范围: 5012/5012
     - 授权对象: 0.0.0.0/0（或指定IP）

### 方法二：手动部署

#### 1. 安装Python3和依赖

**Ubuntu/Debian:**
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv
```

**CentOS/RHEL:**
```bash
yum install -y python3 python3-pip
```

#### 2. 创建项目目录
```bash
mkdir -p /opt/dd_fast
cd /opt/dd_fast
```

#### 3. 上传项目文件
```bash
# 在本地执行
scp -r . root@your-server-ip:/opt/dd_fast/
```

#### 4. 创建虚拟环境并安装依赖
```bash
cd /opt/dd_fast
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask==2.3.3 flask-cors==4.0.0 pymysql==1.1.0 requests pandas openpyxl Pillow openai chuidi_zipcode python-docx
deactivate
```

**注意**: `rumps`是macOS特定的库，在Linux上不需要安装。

#### 5. 创建必要的目录
```bash
mkdir -p /opt/dd_fast/logs
mkdir -p /opt/dd_fast/feature/feishu/currency\ maintenance
mkdir -p /opt/dd_fast/feature/feishu/update\ log
```

#### 6. 安装systemd服务
```bash
# 复制服务文件
cp deploy/dd_fast.service /etc/systemd/system/

# 重新加载systemd
systemctl daemon-reload

# 启用服务（开机自启）
systemctl enable dd_fast

# 启动服务
systemctl start dd_fast
```

#### 7. 配置防火墙

**如果使用firewalld (CentOS):**
```bash
firewall-cmd --permanent --add-port=5012/tcp
firewall-cmd --reload
```

**如果使用ufw (Ubuntu):**
```bash
ufw allow 5012/tcp
ufw reload
```

#### 8. 配置阿里云安全组
- 登录阿里云控制台
- 进入ECS实例 -> 安全组 -> 配置规则
- 添加入方向规则：TCP协议，端口5012

## 服务管理

### 启动/停止/重启服务
```bash
systemctl start dd_fast      # 启动
systemctl stop dd_fast       # 停止
systemctl restart dd_fast    # 重启
systemctl status dd_fast     # 查看状态
```

### 查看日志
```bash
# 查看systemd日志
journalctl -u dd_fast -f

# 查看应用日志
tail -f /opt/dd_fast/logs/server.log
```

### 查看服务状态
```bash
systemctl status dd_fast
```

## 验证部署

1. **检查服务状态**
   ```bash
   systemctl status dd_fast
   ```

2. **测试健康检查接口**
   ```bash
   curl http://localhost:5012/api/health
   ```
   应该返回: `{"status":"ok"}`

3. **测试飞书Webhook接口**
   ```bash
   curl -X POST http://localhost:5012/api/feishu-webhook \
     -H "Content-Type: application/json" \
     -d '{"adjustment_text": "CARD\nUSD - 20%：40%：40%", "adjustment_mode": "update"}'
   ```

4. **从外部访问**
   将`localhost`替换为服务器的公网IP进行测试。

## 配置飞书Webhook

在飞书机器人配置中，将Webhook地址设置为：
```
http://your-server-ip:5012/api/feishu-webhook
```

## 故障排除

### 1. 服务无法启动

**检查日志:**
```bash
journalctl -u dd_fast -n 50
tail -f /opt/dd_fast/logs/server.log
```

**常见问题:**
- 端口被占用: 使用 `lsof -i :5012` 或 `netstat -tulpn | grep 5012` 查看
- 依赖缺失: 检查虚拟环境中是否安装了所有依赖
- 权限问题: 确保服务文件中的路径正确

### 2. 无法从外部访问

**检查:**
1. 服务是否运行: `systemctl status dd_fast`
2. 防火墙规则: `firewall-cmd --list-ports` 或 `ufw status`
3. 阿里云安全组规则是否配置正确
4. 服务器是否有公网IP

### 3. 依赖安装失败

如果某些依赖安装失败，可以尝试：
```bash
source /opt/dd_fast/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

注意：`rumps`是macOS特定的，在Linux上会安装失败，这是正常的。

## 更新部署

当需要更新代码时：

1. **上传新代码**
   ```bash
   scp -r . root@your-server-ip:/tmp/dd_fast
   ```

2. **停止服务**
   ```bash
   systemctl stop dd_fast
   ```

3. **备份并更新文件**
   ```bash
   cd /opt/dd_fast
   cp -r . ../dd_fast_backup_$(date +%Y%m%d_%H%M%S)
   rsync -av --exclude='venv' --exclude='logs' /tmp/dd_fast/ /opt/dd_fast/
   ```

4. **更新依赖（如果需要）**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   deactivate
   ```

5. **重启服务**
   ```bash
   systemctl start dd_fast
   ```

## 使用Nginx反向代理（可选）

如果需要使用域名访问或HTTPS，可以配置Nginx反向代理：

### 安装Nginx
```bash
# Ubuntu/Debian
apt-get install -y nginx

# CentOS/RHEL
yum install -y nginx
```

### 配置Nginx
创建配置文件 `/etc/nginx/sites-available/dd_fast`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5012;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:
```bash
ln -s /etc/nginx/sites-available/dd_fast /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## 安全建议

1. **使用非root用户运行服务**
   - 创建专用用户: `useradd -r -s /bin/false dd_fast`
   - 修改服务文件中的`User`字段

2. **配置HTTPS**
   - 使用Let's Encrypt免费证书
   - 配置Nginx SSL

3. **限制访问IP**
   - 在安全组中只允许特定IP访问
   - 使用防火墙规则限制

4. **定期备份**
   - 备份配置文件和数据目录
   - 设置自动备份任务

## 联系支持

如果遇到问题，请检查：
1. 服务日志: `journalctl -u dd_fast -f`
2. 应用日志: `/opt/dd_fast/logs/server.log`
3. 系统资源: `top`, `df -h`, `free -h`

