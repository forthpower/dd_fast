## 文件批量复制器 (macOS 菜单栏应用)

一个极简的菜单栏小工具：在右上角显示图标，点击打开文件复制功能，批量生成多语言命名的副本。

### 一键运行（开发态）

```bash
python3 /Users/centurygame/PycharmProjects/dd_fast/app.py
```

运行后会在屏幕右上角显示一个绿色方块图标。

### 打包为 macOS 应用 (.app)

```bash
bash /Users/centurygame/PycharmProjects/dd_fast/build_mac.sh
```

完成后，应用位于：

```
/Users/centurygame/PycharmProjects/dd_fast/dist/文件批量复制器.app
```

首次运行若提示「无法打开」：
- 在 Finder 里右键 `打开`，或在「系统设置 -> 隐私与安全性」中允许。

### 使用说明

**菜单栏操作：**
- 点击右上角的绿色方块图标
- 在弹出的菜单中点击「打开文件复制器」打开主窗口
- 点击「退出」关闭应用
- 鼠标悬停在图标上会显示提示信息

**文件复制功能：**
- 选择目标目录（会自动扫描并列出文件）
- 也可以手动追加文件到列表
- 在语言区域勾选需要的语言
- 点击「预览」查看将生成的文件名
- 点击「执行复制」生成副本（已存在会跳过）

### 依赖
- Python 3（macOS 自带或从 `https://www.python.org` 安装）
- 打包依赖：PyInstaller（脚本会自动安装）


