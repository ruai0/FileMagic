# FileMagic 发布与更新操作指南

## 一、用户使用方式

### 方式1：下载EXE（推荐用户使用）

从 GitHub/Gitee Releases 下载打包好的 EXE 文件，双击直接运行，无需安装任何依赖。

### 方式2：下载源代码运行

```bash
# 1. 下载代码
git clone https://github.com/ruai0/FileMagic.git

# 2. 进入目录
cd FileMagic

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行
python main.py
```

## 二、开源发布

### 1. 创建仓库

**GitHub:**
1. 登录 https://github.com
2. 点击 "+" → "New repository"
3. 填写：
   - Repository name: `FileMagic`
   - 选择 Public
4. 点击 "Create repository"

**Gitee:**
1. 登录 https://gitee.com
2. 点击 "+" → "新建仓库"
3. 填写：
   - 仓库名称: `FileMagic`
   - 选择 公开
4. 点击 "创建"

### 2. 上传代码

```bash
cd FileMagic

git init
git remote add origin https://github.com/ruai0/FileMagic.git

git add .
git commit -m "FileMagic v1.0.0"
git push -u origin main
```

### 3. 打包软件

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "FileMagic" main.py
```

### 4. 创建 Release

1. 点击 "Releases" → "Create a new release"
2. 填写：
   - Tag: `v1.0.0`
   - Title: `FileMagic v1.0.0`
   - Description: 更新内容
3. 上传 `dist/FileMagic.exe`
4. 点击 "Publish release"

---

## 二、配置更新功能

### 1. 修改配置

编辑 `ui/github_market.py`，修改为你的信息：

```python
class PluginMarketDialog(QDialog):
    GITHUB_USER = "ruai0"      # 改这里
    GITHUB_REPO = "FileMagic"      # 改这里
    
    GITEE_USER = "ruai0"       # 改这里
    GITEE_REPO = "FileMagic"       # 改这里
```

### 2. 测试更新

- 打开软件 → 帮助 → 检查更新
- 可以切换 GitHub/Gitee 源

---

## 三、发布插件

### 1. 插件目录结构

```
plugins/你的插件名/
├── __init__.py      # 必需
├── plugin.py        # 必需 - 逻辑+UI
└── plugin.json      # 必需 - 配置
```

### 2. plugin.json 示例

```json
{
    "name": "插件名称",
    "description": "插件描述",
    "version": "1.0.0",
    "author": "作者",
    "category": "Excel处理",
    "icon": "plugin",
    "enabled": true
}
```

### 3. plugin.py 示例

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from core.plugin_manager import BasePlugin

class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "我的插件"
        self.description = "插件描述"
        self.category = "Excel处理"
        self._widget = None
    
    def get_widget(self):
        if self._widget is None:
            self._widget = self._create_widget()
        return self._widget
    
    def _create_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("插件界面"))
        return widget
```

### 4. 上传插件

```bash
git add plugins/你的插件名/
git commit -m "添加插件: 你的插件名"
git push
```

### 5. 用户安装

用户在软件中点击 "帮助" → "插件市场" → 找到插件 → 点击 "安装"

---

## 四、发布更新

### 1. 修改代码

修改代码，修复bug或添加功能。

### 2. 更新版本号

在 `main.py` 或相关文件中更新版本号。

### 3. 打包并发布

```bash
# 打包
pyinstaller --onefile --windowed --name "FileMagic" main.py

# 在GitHub/Gitee创建新Release，上传exe
```

### 4. 用户更新

用户打开软件 → 帮助 → 检查更新 → 下载更新包

---

## 五、常见问题

**Q: 插件需要单独发布吗？**
A: 不需要，插件放在仓库的 `plugins/` 目录下，用户通过插件市场安装。

**Q: GitHub和Gitee可以同时用吗？**
A: 可以，软件支持切换更新源。

**Q: 插件UI怎么写？**
A: 直接写在 `plugin.py` 里，使用PyQt6组件。

**Q: 新插件需要新依赖怎么办？**
A: 在插件的 `plugin.json` 中添加 `dependencies` 字段，用户安装插件时会自动安装依赖。

**Q: 用户怎么获取最新版？**
A: 下载EXE用户：重新下载Release。源码用户：`git pull && pip install -r requirements.txt`

**Q: 壳和插件的依赖有什么区别？**
A: 壳只带核心依赖（PyQt6、pandas等），插件的依赖由插件自行声明，安装插件时自动安装。
