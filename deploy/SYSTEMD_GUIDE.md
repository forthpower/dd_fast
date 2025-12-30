# Systemd 服务管理指南

## 一、安装和启动服务

### 方法1: 使用部署脚本（推荐）

```bash
cd /opt/dd_fast
sudo ./deploy/deploy.sh
```

部署脚本会自动：
- 安装 systemd 服务
- 启用开机自启
- 启动服务

### 方法2: 手动安装

```bash
# 1. 复制服务文件
sudo cp /opt/dd_fast/deploy/dd_fast.service /etc/systemd/system/

# 2. 重新加载 systemd
sudo systemctl daemon-reload

# 3. 启用服务（开机自启）
sudo systemctl enable dd_fast

# 4. 启动服务
sudo systemctl start dd_fast
```

## 二、服务管理命令

### 启动服务
```bash
sudo systemctl start dd_fast
```

### 停止服务
```bash
sudo systemctl stop dd_fast
```

### 重启服务
```bash
sudo systemctl restart dd_fast
```

### 查看服务状态
```bash
sudo systemctl status dd_fast
```

### 查看服务是否运行
```bash
sudo systemctl is-active dd_fast
```

### 查看服务是否已启用（开机自启）
```bash
sudo systemctl is-enabled dd_fast
```

## 三、查看日志

### 查看实时日志
```bash
sudo journalctl -u dd_fast -f
```

### 查看最近50条日志
```bash
sudo journalctl -u dd_fast -n 50
```

### 查看今天的日志
```bash
sudo journalctl -u dd_fast --since today
```

### 查看应用日志文件
```bash
tail -f /opt/dd_fast/logs/server.log
```

## 四、服务配置说明

### 服务文件位置
```
/etc/systemd/system/dd_fast.service
```

### 关键配置项

- **ExecStart**: `/opt/dd_fast/venv/bin/python3 /opt/dd_fast/app.py`
  - 使用虚拟环境中的 Python
  - 启动 `app.py` 脚本

- **Restart=always**: 服务异常退出时自动重启

- **RestartSec=10**: 重启前等待10秒

- **WorkingDirectory**: `/opt/dd_fast`
  - 服务的工作目录

## 五、验证服务运行

### 1. 检查服务状态
```bash
sudo systemctl status dd_fast
```

应该看到：
```
Active: active (running) since ...
```

### 2. 测试API接口
```bash
# 健康检查
curl http://localhost:5012/api/health

# 应该返回: {"status":"ok"}
```

### 3. 检查端口占用
```bash
sudo lsof -i :5012
# 或
sudo netstat -tulpn | grep 5012
```

## 六、常见问题

### Q1: 服务无法启动

**查看详细错误:**
```bash
sudo journalctl -u dd_fast -n 50
```

**常见原因:**
1. Python 路径错误
2. 虚拟环境未创建
3. 依赖未安装
4. 端口被占用

**解决方法:**
```bash
# 检查虚拟环境
ls -la /opt/dd_fast/venv/bin/python3

# 检查依赖
/opt/dd_fast/venv/bin/pip list

# 检查端口
sudo lsof -i :5012
```

### Q2: 服务启动后立即退出

**查看日志:**
```bash
sudo journalctl -u dd_fast -n 100 --no-pager
```

**可能原因:**
- `app.py` 脚本有错误
- 缺少依赖
- 权限问题

**解决方法:**
```bash
# 手动测试运行
cd /opt/dd_fast
/opt/dd_fast/venv/bin/python3 app.py

# 查看具体错误信息
```

### Q3: 服务无法自动重启

**检查配置:**
```bash
sudo systemctl cat dd_fast | grep Restart
```

应该看到 `Restart=always`

**如果配置正确但仍不重启:**
```bash
# 重新加载配置
sudo systemctl daemon-reload
sudo systemctl restart dd_fast
```

### Q4: 修改服务配置后不生效

**解决方法:**
```bash
# 1. 修改服务文件
sudo nano /etc/systemd/system/dd_fast.service

# 2. 重新加载 systemd
sudo systemctl daemon-reload

# 3. 重启服务
sudo systemctl restart dd_fast
```

## 七、自定义配置

### 修改服务配置

```bash
# 编辑服务文件
sudo nano /etc/systemd/system/dd_fast.service
```

### 常用修改项

**1. 修改运行用户（推荐使用非root用户）**
```ini
[Service]
User=www-data  # 或其他非root用户
Group=www-data
```

**2. 修改环境变量**
```ini
[Service]
Environment="PYTHONPATH=/opt/dd_fast"
Environment="LOG_LEVEL=INFO"
```

**3. 修改重启策略**
```ini
[Service]
Restart=on-failure  # 只在失败时重启
RestartSec=5       # 等待5秒后重启
```

**4. 限制资源使用**
```ini
[Service]
LimitNOFILE=65536
MemoryLimit=512M
CPUQuota=50%
```

修改后记得：
```bash
sudo systemctl daemon-reload
sudo systemctl restart dd_fast
```

## 八、卸载服务

### 停止并禁用服务
```bash
sudo systemctl stop dd_fast
sudo systemctl disable dd_fast
```

### 删除服务文件
```bash
sudo rm /etc/systemd/system/dd_fast.service
sudo systemctl daemon-reload
```

### 删除项目文件（可选）
```bash
sudo rm -rf /opt/dd_fast
```

## 九、服务状态监控

### 创建监控脚本

```bash
#!/bin/bash
# /opt/dd_fast/check_service.sh

if ! systemctl is-active --quiet dd_fast; then
    echo "服务未运行，正在重启..."
    systemctl restart dd_fast
    sleep 5
    if systemctl is-active --quiet dd_fast; then
        echo "服务已重启成功"
    else
        echo "服务重启失败，请检查日志"
        journalctl -u dd_fast -n 20
    fi
fi
```

### 添加到 crontab（可选）

```bash
# 每5分钟检查一次
*/5 * * * * /opt/dd_fast/check_service.sh >> /var/log/dd_fast_check.log 2>&1
```

## 十、快速参考

```bash
# 启动
sudo systemctl start dd_fast

# 停止
sudo systemctl stop dd_fast

# 重启
sudo systemctl restart dd_fast

# 状态
sudo systemctl status dd_fast

# 日志
sudo journalctl -u dd_fast -f

# 启用开机自启
sudo systemctl enable dd_fast

# 禁用开机自启
sudo systemctl disable dd_fast

# 重新加载配置
sudo systemctl daemon-reload
```

