# Schema Generator

可视化的 Schema 生成器，快速创建和管理数据模型配置。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python3 app.py

# 访问 http://localhost:5010
```

## 功能特性

- 🎨 **可视化配置** - 直观的图形界面配置模型、字段、动作
- 📝 **字段管理** - 支持多种字段类型（String, Integer, Select, File等）
- 🔄 **动作配置** - 灵活配置 CRUD 操作和自定义动作
- 📥 **批量导入** - 从文件夹批量导入 Python schema 文件
- 🔄 **自动同步** - 将修改自动同步回源文件

## 项目结构

```
schema_generator/
├── app.py                      # Flask 应用（983行）
├── static/                     # 前端资源
│   ├── index.html             # 主页面
│   └── script.js              # JavaScript 逻辑（3985行）
├── models/                     # Schema 示例
├── models.db                   # SQLite 数据库
└── requirements.txt            # Python 依赖
```

## 使用指南

### 基础使用

1. **创建模型** - 点击"新增模型"配置基本信息
2. **配置字段** - 添加字段并设置类型和属性
3. **配置动作** - 选择需要的操作（列表/创建/编辑/删除）
4. **生成代码** - 生成 Python schema 代码

### 批量导入

1. 点击"从文件导入" → 选择"批量导入(文件夹)"
2. 输入包含 `.py` schema 文件的文件夹路径
3. 系统自动解析并导入所有模型
4. 自动识别父菜单结构

### 自动同步

1. 通过"批量导入"功能导入的模型会记录源文件路径
2. 在界面中编辑模型配置
3. 点击"🔄 自动同步"按钮
4. 修改自动写回到源文件（会自动备份原文件为 `.backup`）

## 技术栈

- **前端**: Vanilla JavaScript + CSS3
- **后端**: Python Flask
- **数据库**: SQLite

## 开发

### 添加新功能

在 `app.py` 中添加路由，在 `static/script.js` 中添加前端逻辑。

## License

MIT
