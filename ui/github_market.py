import os
import json
import zipfile
import urllib.request
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QMessageBox, QWidget,
    QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class GitHubDownloader(QThread):
    """GitHub下载线程"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
    
    def run(self):
        try:
            self.progress.emit(0, "开始下载...")
            
            req = urllib.request.Request(self.url, headers={"User-Agent": "FileMagic"})
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = response.headers.get("content-length", 0)
                downloaded = 0
                
                with open(self.save_path, "wb") as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size:
                            progress = int(downloaded / int(total_size) * 100)
                            self.progress.emit(progress, f"下载中... {downloaded}/{total_size}")
                
                self.finished.emit(True, "下载完成")
        
        except Exception as e:
            self.finished.emit(False, f"下载失败: {str(e)}")


class PluginMarketDialog(QDialog):
    """插件市场对话框 - 支持同仓库管理插件和软件更新"""
    
    # ====== 配置区域 - 请修改为你的信息 ======
    GITHUB_USER = "ruai0"
    GITHUB_REPO = "FileMagic"
    
    GITEE_USER = "ruai0"
    GITEE_REPO = "FileMagic"
    # ====== 配置区域结束 ======
    
    def __init__(self, plugins_dir: str, parent=None):
        super().__init__(parent)
        self.plugins_dir = plugins_dir
        self.current_platform = "github"
        self.setWindowTitle("插件市场")
        self.setMinimumSize(750, 550)
        self.available_plugins = []
        self._setup_ui()
        self._load_plugins()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        title = QLabel("📦 插件市场")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title)
        
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("平台:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["GitHub", "Gitee"])
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(self.platform_combo)
        header.addLayout(platform_layout)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._load_plugins)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        self.status_label = QLabel("正在加载插件列表...")
        self.status_label.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["名称", "版本", "描述", "下载量", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _on_platform_changed(self, index):
        """平台切换"""
        self.current_platform = "github" if index == 0 else "gitee"
        self._load_plugins()
    
    def _get_api_url(self):
        """获取API地址 - 从仓库的plugins目录获取插件"""
        if self.current_platform == "github":
            return f"https://api.github.com/repos/{self.GITHUB_USER}/{self.GITHUB_REPO}/contents/plugins"
        else:
            return f"https://gitee.com/api/v5/repos/{self.GITEE_USER}/{self.GITEE_REPO}/contents/plugins"
    
    def _load_plugins(self):
        """从云端加载插件列表"""
        self.status_label.setText("正在获取插件列表...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        api_url = self._get_api_url()
        
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "FileMagic"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                self.available_plugins = []
                for item in data:
                    if item["type"] == "dir":
                        self.available_plugins.append({
                            "name": item["name"],
                            "path": item["path"],
                            "download_url": item.get("download_url"),
                            "size": item.get("size", 0)
                        })
                
                self.progress_bar.setValue(100)
                self.status_label.setText(f"找到 {len(self.available_plugins)} 个可用插件")
                self._update_table()
        
        except urllib.error.URLError:
            self.status_label.setText("无法连接到服务器，请检查网络")
            self.progress_bar.setValue(0)
            self._load_local_plugins()
        
        except Exception as e:
            self.status_label.setText(f"加载失败: {str(e)}")
            self.progress_bar.setValue(0)
            self._load_local_plugins()
    
    def _load_local_plugins(self):
        """加载本地插件列表（离线模式）"""
        self.available_plugins = []
        plugins_path = os.path.join(self.plugins_dir)
        
        if os.path.exists(plugins_path):
            for item in os.listdir(plugins_path):
                plugin_dir = os.path.join(plugins_path, item)
                if os.path.isdir(plugin_dir):
                    plugin_json_path = os.path.join(plugin_dir, "plugin.json")
                    if os.path.exists(plugin_json_path):
                        try:
                            with open(plugin_json_path, "r", encoding="utf-8") as f:
                                config = json.load(f)
                                self.available_plugins.append({
                                    "name": config.get("name", item),
                                    "description": config.get("description", ""),
                                    "version": config.get("version", "1.0.0"),
                                    "downloads": 0
                                })
                        except:
                            self.available_plugins.append({
                                "name": item,
                                "description": "",
                                "version": "1.0.0",
                                "downloads": 0
                            })
        
        if not self.available_plugins:
            self.status_label.setText("没有安装任何插件")
        else:
            self.status_label.setText(f"离线模式：显示 {len(self.available_plugins)} 个已安装插件")
        self._update_table()
    
    def _update_table(self):
        """更新表格"""
        self.table.setRowCount(len(self.available_plugins))
        
        for i, plugin in enumerate(self.available_plugins):
            self.table.setItem(i, 0, QTableWidgetItem(plugin.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(plugin.get("version", "1.0.0")))
            self.table.setItem(i, 2, QTableWidgetItem(plugin.get("description", "")))
            self.table.setItem(i, 3, QTableWidgetItem(str(plugin.get("downloads", 0))))
            
            install_btn = QPushButton("安装")
            install_btn.clicked.connect(lambda checked, p=plugin: self._install_plugin(p))
            self.table.setCellWidget(i, 4, install_btn)
    
    def _install_plugin(self, plugin: Dict):
        """安装插件"""
        reply = QMessageBox.question(
            self, "安装插件",
            f"确定要安装插件 '{plugin['name']}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.status_label.setText(f"正在安装: {plugin['name']}...")
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            
            if plugin.get("download_url"):
                save_path = os.path.join(self.plugins_dir, f"{plugin['name']}.zip")
                self.downloader = GitHubDownloader(plugin["download_url"], save_path)
                self.downloader.progress.connect(self._on_download_progress)
                self.downloader.finished.connect(self._on_download_finished)
                self.downloader.start()
            else:
                self.status_label.setText("插件暂不支持在线安装")
                self.progress_bar.setVisible(False)
    
    def _install_dependencies(self, plugin_name: str):
        """安装插件依赖"""
        plugin_json = os.path.join(self.plugins_dir, plugin_name, "plugin.json")
        
        if not os.path.exists(plugin_json):
            return
        
        try:
            with open(plugin_json, "r", encoding="utf-8") as f:
                config = json.load(f)
                dependencies = config.get("dependencies", [])
            
            if dependencies:
                self.status_label.setText(f"正在安装依赖...")
                
                for dep in dependencies:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep],
                        capture_output=True
                    )
                
                self.status_label.setText("依赖安装完成")
        except Exception as e:
            self.status_label.setText(f"依赖安装失败: {str(e)}")
    
    def _on_download_progress(self, progress: int, message: str):
        """下载进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_download_finished(self, success: bool, message: str):
        """下载完成"""
        if success:
            self.status_label.setText("插件下载完成，正在安装依赖...")
            self.progress_bar.setValue(80)
            
            plugin_name = os.path.basename(self.current_plugin_name) if hasattr(self, 'current_plugin_name') else ""
            if plugin_name:
                self._install_dependencies(plugin_name)
            
            self.status_label.setText("安装完成!")
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "完成", "插件安装成功！请重启应用。")
        else:
            self.status_label.setText(message)
            QMessageBox.warning(self, "失败", message)


class UpdateChecker(QThread):
    """更新检查线程"""
    
    update_found = pyqtSignal(str, str, str)
    check_complete = pyqtSignal(bool, str)
    
    # ====== 配置区域 - 请修改为你的信息 ======
    GITHUB_USER = "ruai0"
    GITHUB_REPO = "FileMagic"
    
    GITEE_USER = "ruai0"
    GITEE_REPO = "FileMagic"
    # ====== 配置区域结束 ======
    
    def __init__(self, current_version: str, platform: str = "github"):
        super().__init__()
        self.current_version = current_version
        self.platform = platform
    
    def run(self):
        try:
            if self.platform == "github":
                url = f"https://api.github.com/repos/{self.GITHUB_USER}/{self.GITHUB_REPO}/releases/latest"
            else:
                url = f"https://gitee.com/api/v5/repos/{self.GITEE_USER}/{self.GITEE_REPO}/releases/latest"
            
            req = urllib.request.Request(url, headers={"User-Agent": "FileMagic"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get("tag_name", "").lstrip("v")
                release_notes = data.get("body", "")
                download_url = None
                
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe") or asset["name"].endswith(".zip"):
                        download_url = asset["browser_download_url"]
                        break
                
                if self._version_compare(latest_version, self.current_version) > 0:
                    self.update_found.emit(latest_version, release_notes, download_url or "")
                else:
                    self.check_complete.emit(True, "已是最新版本")
        
        except urllib.error.URLError:
            self.check_complete.emit(False, "无法连接到更新服务器")
        
        except Exception as e:
            self.check_complete.emit(False, f"检查失败: {str(e)}")
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """比较版本号"""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
        except:
            pass
        return 0


class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.download_url = None
        self.platform = "github"
        self.setWindowTitle("检查更新")
        self.setMinimumSize(450, 350)
        self._setup_ui()
        self._start_check()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("🔄 检查更新")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        version_info = QLabel(f"当前版本: v{self.current_version}")
        version_info.setStyleSheet("font-size: 14px; padding: 10px 0;")
        layout.addWidget(version_info)
        
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("更新源:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["GitHub", "Gitee"])
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        platform_layout.addWidget(self.platform_combo)
        platform_layout.addStretch()
        layout.addLayout(platform_layout)
        
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setStyleSheet("padding: 20px; color: #888;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.notes_label = QLabel("")
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet("padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px;")
        self.notes_label.setVisible(False)
        layout.addWidget(self.notes_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.close_btn)
        
        self.download_btn = QPushButton("下载更新")
        self.download_btn.setStyleSheet("background-color: #00d4aa; color: white; padding: 8px 20px;")
        self.download_btn.setVisible(False)
        self.download_btn.clicked.connect(self._download_update)
        buttons_layout.addWidget(self.download_btn)
        
        layout.addLayout(buttons_layout)
    
    def _on_platform_changed(self, index):
        """平台切换"""
        self.platform = "github" if index == 0 else "gitee"
        self._start_check()
    
    def _start_check(self):
        """开始检查更新"""
        self.status_label.setText("正在检查更新...")
        self.status_label.setStyleSheet("padding: 20px; color: #888;")
        self.notes_label.setVisible(False)
        self.download_btn.setVisible(False)
        
        self.checker = UpdateChecker(self.current_version, self.platform)
        self.checker.update_found.connect(self._on_update_found)
        self.checker.check_complete.connect(self._on_check_complete)
        self.checker.start()
    
    def _on_update_found(self, version: str, notes: str, download_url: str):
        """发现新版本"""
        self.status_label.setText(f"🎉 发现新版本: v{version}")
        self.status_label.setStyleSheet("padding: 20px; color: #00d4aa; font-weight: bold; font-size: 16px;")
        
        if notes:
            self.notes_label.setText(f"更新内容:\n{notes[:500]}")
            self.notes_label.setVisible(True)
        
        self.download_url = download_url
        self.download_btn.setVisible(True)
    
    def _on_check_complete(self, success: bool, message: str):
        """检查完成"""
        self.status_label.setText(message)
        if success:
            self.status_label.setStyleSheet("padding: 20px; color: #00d4aa; font-size: 14px;")
        else:
            self.status_label.setStyleSheet("padding: 20px; color: #ff6b6b; font-size: 14px;")
    
    def _download_update(self):
        """下载更新"""
        if not self.download_url:
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存更新文件", 
            os.path.expanduser("~/Downloads"),
            "ZIP文件 (*.zip);;所有文件 (*)"
        )
        
        if save_path:
            self.progress_bar.setVisible(True)
            self.download_btn.setEnabled(False)
            
            self.downloader = GitHubDownloader(self.download_url, save_path)
            self.downloader.progress.connect(self._on_download_progress)
            self.downloader.finished.connect(self._on_download_finished)
            self.downloader.start()
    
    def _on_download_progress(self, progress: int, message: str):
        """下载进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_download_finished(self, success: bool, message: str):
        """下载完成"""
        if success:
            self.status_label.setText("✅ 下载完成!")
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "完成", 
                "更新包已下载完成。\n\n请解压后运行 setup.exe 进行安装。")
        else:
            self.status_label.setText(f"❌ {message}")
            self.download_btn.setEnabled(True)
