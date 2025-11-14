# dd_fast 多功能工具集

一个基于系统托盘的多功能工具集，包含文件复制器、Workflow编辑器、Schema生成器、命令大全、数据脚本生成器、Workflow可视化工具等功能。

## 快速启动

```bash
python3 app.py
```

运行后会在系统托盘中显示图标，右键点击可看到功能菜单。

> **注意**：首次运行需要安装依赖 `pip3 install rumps flask flask-cors python-docx`

## 打包为 macOS 应用 (.app)

### 快速打包
```bash
bash system/build_mac.sh
```

### 打包结果
- 应用位置：`dist/dd_fast.app`
- 应用大小：约18MB
- 支持架构：Apple Silicon (ARM64) 和 Intel Mac

### 首次运行
若提示「无法打开」：
- 在 Finder 里右键选择「打开」
- 或在「系统设置 -> 隐私与安全性」中允许运行

## 使用说明

### 系统托盘操作
右键点击系统托盘中的图标，在弹出的菜单中选择功能：

- **文件复制器** - 批量生成多语言命名的文件副本
- **Workflow编辑器** - 可视化工作流编辑器  
- **Schema生成器** - 数据库Schema生成工具
- **命令大全** - 常用命令查询工具
- **数据脚本生成器** - 自定义生成Python数据操作脚本
- **Workflow可视化** - 可视化查看和分析Workflow JSON文件
- **退出** - 关闭应用

### 功能详情

- **文件复制器**：选择目标目录，勾选语言，批量生成多语言文件副本
- **Workflow编辑器**：在浏览器中打开可视化工作流编辑界面
- **Schema生成器**：在浏览器中打开数据库Schema生成工具
- **命令大全**：打开常用命令查询工具
- **数据脚本生成器**：自定义表字段和功能，生成Python数据操作脚本
- **Workflow可视化**：上传Workflow JSON文件，直观查看节点、条件和连接关系

## 飞书Webhook集成

### 功能说明

程序启动后会自动启动一个HTTP服务器，持续运行并随时接收飞书机器人发送的Webhook请求。

### 服务器信息

- **端口**: 5012
- **Webhook地址**: `http://your-server-ip:5012/api/feishu-webhook`
- **健康检查**: `http://your-server-ip:5012/api/health`
- **Web界面**: `http://localhost:5012/`

### 使用方法

1. **启动程序**：运行 `python3 app.py` 或启动打包后的应用
2. **服务器自动启动**：程序启动时会自动在后台启动Webhook服务器
3. **配置飞书机器人**：在飞书机器人设置中配置Webhook地址为你的服务器地址
4. **发送请求**：飞书机器人可以通过POST请求发送调整方案

### Webhook请求格式

```json
{
  "adjustment_text": "CARD\nUSD - 20%：40%：40%\nEUR - 30%：30%：40%",
  "adjustment_mode": "update"
}
```

### 返回格式

```json
{
  "success": true,
  "steps": "调整步骤描述..."
}
```

### 特性

- **持续运行**：服务器在后台持续运行，随时接收请求
- **自动重启**：如果服务器崩溃，会自动重试启动（最多5次）
- **详细日志**：记录所有Webhook请求和处理过程
- **错误处理**：完善的错误处理和错误信息返回
- **多线程支持**：支持并发处理多个请求

### 注意事项

- 确保防火墙允许5012端口的访问
- 如果端口被占用，程序会提示错误信息
- 所有Webhook请求都会记录在日志中
- 服务器运行在 `0.0.0.0`，可以从任何IP访问

## Workflow可视化工具详细说明

### 功能特性

Workflow工具集提供两个主要功能：

#### 1. Workflow可视化
- **Web界面**：现代化的HTML界面，整洁美观
- **文件上传**：支持拖拽或点击上传JSON文件
- **直观可视化**：美观的卡片式界面展示工作流节点
- **Split分析**：专门展示Split节点的分量分布情况
- **实时统计**：显示节点总数、连接数和Split数
- **详细信息**：点击节点查看完整信息和原始数据
- **智能解析**：自动解析节点、条件、分支结构

#### 2. 分量对比分析
- **自动读取文档**：自动读取项目中的Primer Workflow文档
- **调整方案输入**：输入分量调整方案文本
- **两种调整模式**：
  - **更新调整**：只调整指定币种，其他保持原样
  - **覆盖调整**：全部按照新方案设置
- **完整对比展示**：
  - 显示需要添加的币种（一行展示多个）
  - 显示需要删除的币种（一行展示多个）
  - 显示需要修改的币种（显示原来的和现在的分量）
  - 显示完整的分量对比表格（之前 vs 现在）
- **币种合并**：相同分量的币种自动合并显示（用'/'分隔）

### 使用方法

#### Workflow可视化
1. 从主应用菜单选择 "Workflow可视化"
2. 在Web界面中上传JSON文件
3. 查看节点、连接和Split分布
4. 点击节点查看详细信息

#### 分量对比分析
1. 从主应用菜单选择 "Workflow可视化"
2. 切换到"分量对比分析"标签
3. 输入调整方案文本，格式示例：
   ```
   CARD
   USD - 20%：40%：40%
   KRW/EUR/AED - 40%：20%：40%
   JPY - 20%：20%：60%
   ```
4. 选择调整模式（更新调整/覆盖调整）
5. 点击"开始对比"查看结果

### 支持的Workflow格式

支持 Primer Workflow 导出的 JSON 格式，包括：
- Trigger 节点
- Component 节点（API调用等）
- Action 节点
- Conditional outcomes（条件分支）
- Default outcomes（默认分支）
- 复杂嵌套条件
- ROUTE_SPLITTER 节点（分量分配）

### 技术栈

- **后端**：Python 3.11+, Flask, Flask-CORS, python-docx
- **前端**：HTML5 + CSS3 + Vanilla JavaScript
- **数据格式**：JSON, DOCX

## 数据脚本生成器详细说明

### 功能特性
- **纯脚本生成**: 无需数据库连接，直接生成可用的Python脚本
- **自定义字段配置**: 自由定义表字段和数据类型
- **功能选择**: 选择你需要的CRUD操作功能
- **Python脚本生成**: 自动生成完整的Python数据操作脚本
- **现代化界面**: 基于Web的直观操作界面

### 使用方法
1. 从主应用菜单选择 "数据脚本生成器"
2. 在Web界面中配置表信息和字段
3. 选择需要的CRUD操作功能
4. 点击生成Python脚本
5. 复制生成的脚本到你的项目中使用

### 生成的脚本特性
- 使用 `pymysql` 库连接MySQL
- 包含完整的错误处理和字段验证
- 支持字典形式的结果返回
- 自动连接管理和资源清理
- 包含完整的使用示例代码

## 自启动和自动重启

### 功能说明

程序支持开机自启动和自动重启功能：
- **开机自启动**：系统登录时自动启动程序
- **自动重启**：如果程序意外停止，守护进程会自动重启
- **后台运行**：无需打开IDE或终端，程序在后台持续运行

### 安装自启动

1. **运行安装脚本**：
   ```bash
   bash system/install_autostart.sh
   ```

2. **验证安装**：
   ```bash
   launchctl list | grep com.ddfast.daemon
   ```

3. **查看日志**：
   ```bash
   tail -f ~/Library/Logs/dd_fast/daemon.log
   ```

### 管理自启动服务

**立即启动服务**（不等待重启）：
```bash
launchctl load ~/Library/LaunchAgents/com.ddfast.daemon.plist
```

**停止服务**：
```bash
launchctl unload ~/Library/LaunchAgents/com.ddfast.daemon.plist
```

**重启服务**：
```bash
launchctl unload ~/Library/LaunchAgents/com.ddfast.daemon.plist
launchctl load ~/Library/LaunchAgents/com.ddfast.daemon.plist
```

**查看服务状态**：
```bash
launchctl list | grep com.ddfast.daemon
```

**卸载自启动**：
```bash
bash system/uninstall_autostart.sh
```

### 工作原理

1. **守护进程** (`system/daemon.py`)：
   - 监控主程序运行状态
   - 每10秒检查一次进程是否运行
   - 如果程序停止，自动重启（最多重试5次）
   - 记录所有操作到日志文件

2. **LaunchAgent** (`com.ddfast.daemon.plist`)：
   - macOS系统级服务配置
   - 登录时自动启动守护进程
   - 守护进程异常退出时自动重启

### 日志位置

- **守护进程日志**：`~/Library/Logs/dd_fast/daemon.log`
- **守护进程错误日志**：`~/Library/Logs/dd_fast/daemon.error.log`
- **应用输出日志**：`~/Library/Logs/dd_fast/app.stdout.log`
- **应用错误日志**：`~/Library/Logs/dd_fast/app.stderr.log`
- **应用PID文件**：`~/Library/Logs/dd_fast/dd_fast.pid`

**查看日志命令**：
```bash
# 守护进程日志
tail -f ~/Library/Logs/dd_fast/daemon.log

# 应用输出日志
tail -f ~/Library/Logs/dd_fast/app.stdout.log

# 应用错误日志
tail -f ~/Library/Logs/dd_fast/app.stderr.log
```

### 注意事项

- 自启动服务会在用户登录时自动启动，无需手动操作
- 如果程序连续启动失败5次，守护进程会停止尝试，请检查日志
- 卸载自启动服务不会删除日志文件，需要手动清理
- 确保防火墙允许5012端口访问，以便Webhook功能正常工作

## 依赖安装

```bash
pip3 install rumps flask flask-cors python-docx
```

- **rumps** - 系统托盘库
- **flask** - Web框架
- **flask-cors** - 跨域支持
- **python-docx** - DOCX文件读取（用于分量对比功能）

## 故障排除

如果遇到问题：

1. **检查依赖**：
   ```bash
   pip3 install rumps flask flask-cors python-docx
   ```

2. **检查Python版本**：
   ```bash
   python3 --version
   ```

3. **查看错误信息**：
   运行 `python3 app.py` 查看控制台输出的详细错误信息

4. **权限问题**：
   如果打包后的应用无法运行，在Finder中右键选择"打开"

5. **自启动问题**：
   - 检查服务是否运行：`launchctl list | grep com.ddfast.daemon`
   - 查看守护进程日志：`tail -f ~/Library/Logs/dd_fast/daemon.log`
   - 如果服务未运行，重新安装：`bash system/install_autostart.sh`


