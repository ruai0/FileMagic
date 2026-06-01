# FileMagic

全能办公工具集 - 基于 Python + PyQt6 的插件化办公工具

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)

## 简介

FileMagic 是一款功能强大的办公工具集，支持 Excel、PDF、Word、图片等多种文件格式的处理。采用插件化架构，功能易于扩展。

## 功能特性

### 📊 Excel处理（13个插件）

| 插件 | 功能 |
|------|------|
| 文件合并 | 多个Excel文件合并为一个 |
| 文件拆分 | 按工作表/行数/条件拆分 |
| 数据清洗 | 去重、处理空值、去空格 |
| 格式转换 | Excel↔CSV/JSON互转 |
| 数据分析 | 基本统计、透视、相关性 |
| 批量处理 | 批量转换、去空行 |
| 图表生成 | 柱状图/折线图/饼图 |
| 数据筛选 | 多条件组合筛选导出 |
| 工作表管理 | 批量导出/删除/重命名工作表 |
| 数据脱敏 | 手机号、身份证、邮箱脱敏 |
| 数据对比 | 对比两个文件差异 |
| 文件重命名 | 批量重命名Excel文件 |
| Excel转Word | 用Excel数据生成Word报告 |

### 📄 PDF处理（9个插件）

| 插件 | 功能 |
|------|------|
| PDF合并 | 多个PDF合成一个 |
| PDF拆分 | 按页码范围/逐页拆分 |
| PDF转图片 | PDF页面转PNG/JPG |
| 图片转PDF | 多张图片合成PDF |
| PDF提取 | 提取文字和表格 |
| PDF水印 | 添加文字水印 |
| PDF加密 | 设置密码保护 |
| PDF转Excel | 提取PDF表格到Excel |
| PDF压缩 | 压缩PDF文件大小 |

### 📝 Word处理（6个插件）

| 插件 | 功能 |
|------|------|
| Word转PDF | DOCX转PDF |
| Word替换 | 批量查找替换文本 |
| Word提取 | 提取文字、表格、图片 |
| Word合并 | 多个Word合成一个 |
| Word模板填充 | 用数据批量生成报告 |
| Word批量水印 | 批量添加水印 |

### 🖼️ 图片处理（1个插件）

| 插件 | 功能 |
|------|------|
| 图片批量处理 | 压缩、格式转换、调整尺寸 |

### 🛠️ 平台功能

| 功能 | 说明 |
|------|------|
| 收藏夹 | 右键添加常用功能到收藏 |
| 最近使用 | 自动记录最近使用的功能 |
| 深色/亮色模式 | 支持主题切换 |
| 系统托盘 | 最小化到托盘，双击恢复 |
| 快捷键 | Ctrl+1~9 快速访问收藏功能 |
| 设置面板 | 自定义各种设置 |
| 插件市场 | 在线安装插件（支持GitHub/Gitee） |
| 在线更新 | 自动检查新版本（支持GitHub/Gitee） |
| 任务管理器 | 查看任务进度 |
| 操作历史 | 记录所有操作 |
| 批量重命名 | 支持7种重命名模式 |
| 文件预览 | 预览Excel/PDF/Word/文本文件 |
| 国际化支持 | 支持中文/英文切换 |

## 截图

> 待添加

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python main.py
```

### 打包为EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "FileMagic" main.py
```

打包完成后，EXE文件在 `dist/` 目录下。

## 依赖说明

### 核心依赖（壳自带）
```
PyQt6>=6.6.0
openpyxl>=3.1.0
pandas>=2.1.0
chardet>=5.2.0
```

### 插件依赖（按需安装）
每个插件可以声明自己的依赖，安装插件时会自动安装：
- PDF插件：pypdf, PyMuPDF, pdfplumber
- Word插件：python-docx
- 图片插件：Pillow
- 等等...

用户只需安装一次，后续使用无需重复安装。

## 项目结构

```
FileMagic/
├── main.py              # 程序入口
├── core/                # 核心框架
│   ├── app.py           # 主窗口
│   ├── plugin_manager.py
│   ├── config_manager.py
│   └── ...
├── ui/                  # UI组件
│   ├── settings.py
│   ├── task_manager.py
│   └── ...
├── plugins/             # 28个插件
│   ├── file_merger/
│   ├── data_cleaner/
│   └── ...
├── config/              # 配置文件
├── docs/                # 文档
└── resources/           # 资源文件
```

## 插件开发

### 插件结构

```
plugins/my_plugin/
├── __init__.py      # 固定写法
├── plugin.py        # 插件逻辑和UI
└── plugin.json      # 插件配置
```

### plugin.json 示例

```json
{
    "name": "我的插件",
    "description": "插件描述",
    "version": "1.0.0",
    "author": "作者名",
    "category": "Excel处理",
    "icon": "plugin",
    "enabled": true
}
```

### plugin.py 示例

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from core.plugin_manager import BasePlugin

class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "我的插件"
        self.description = "插件描述"
        self.category = "Excel处理"
    
    def get_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("插件界面"))
        return widget
```

详细开发文档请查看 `docs/PUBLISH_GUIDE.md`

## 更新日志

### v1.0.0 (2024-xx-xx)

**新增功能**
- 初始发布
- 28个功能插件
- 18个平台功能

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- GitHub: https://github.com/你的用户名/FileMagic
- Gitee: https://gitee.com/你的用户名/FileMagic
- Email: your-email@example.com

## 致谢

- [Python](https://www.python.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [pandas](https://pandas.pydata.org/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
