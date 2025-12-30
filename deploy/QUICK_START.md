# 快速部署指南

## 一键部署到阿里云ECS

### 步骤1: 上传项目到服务器

在本地项目目录执行：
```bash
# 压缩项目（排除不需要的文件）
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.idea' \
    --exclude='venv' \
    --exclude='*.log' \
    --exclude='logs' \
    --exclude='dd_fast.tar.gz' \
    -czf dd_fast.tar.gz .

# 上传到服务器
scp dd_fast.tar.gz root@42.121.252.52:/root/
```

### 步骤2: SSH登录服务器并部署

```bash
# SSH登录
ssh root@your-server-ip

# 解压项目
cd /root
tar -xzf dd_fast.tar.gz -C /root/dd_fast

# 运行部署脚本
cd /root/dd_fast
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### 步骤3: 配置阿里云安全组

1. 登录阿里云控制台
2. 进入 **ECS实例** -> 选择您的实例 -> **安全组** -> **配置规则**
3. 点击 **添加安全组规则**
4. 配置如下：
   - **规则方向**: 入方向
   - **授权策略**: 允许
   - **协议类型**: 自定义TCP
   - **端口范围**: 5012/5012
   - **授权对象**: 0.0.0.0/0（或指定IP范围）
   - **描述**: dd_fast服务端口

### 步骤4: 验证部署

```bash
# 检查服务状态
systemctl status dd_fast

# 测试健康检查
curl http://localhost:5012/api/health

# 查看日志
journalctl -u dd_fast -f
```

### 步骤5: 配置飞书Webhook

在飞书机器人配置中，将Webhook地址设置为：
```
http://your-server-ip:5012/api/feishu-webhook
```

## 常用命令

```bash
# 服务管理
systemctl start dd_fast      # 启动
systemctl stop dd_fast       # 停止
systemctl restart dd_fast    # 重启
systemctl status dd_fast     # 状态

# 查看日志
journalctl -u dd_fast -f                    # systemd日志
tail -f /opt/dd_fast/logs/server.log        # 应用日志

# 测试接口
curl http://localhost:5012/api/health
```

## 故障排除

### 服务无法启动
```bash
# 查看详细错误
journalctl -u dd_fast -n 50
tail -f /opt/dd_fast/logs/server.log
```

### 端口被占用
```bash
# 查看占用端口的进程
lsof -i :5012
# 或
netstat -tulpn | grep 5012
```

### 无法从外部访问
1. 检查服务是否运行: `systemctl status dd_fast`
2. 检查防火墙: `firewall-cmd --list-ports` 或 `ufw status`
3. 检查阿里云安全组规则
4. 检查服务器是否有公网IP

## 更新代码

```bash
# 1. 上传新代码
scp -r . root@your-server-ip:/root/dd_fast

# 2. 停止服务
systemctl stop dd_fast

# 3. 更新文件
cd /opt/dd_fast
rsync -av --exclude='venv' --exclude='logs' /root/dd_fast/ .

# 4. 更新依赖（如果需要）
source venv/bin/activate
pip install -r requirements-linux.txt
deactivate

# 5. 重启服务
systemctl start dd_fast
```

