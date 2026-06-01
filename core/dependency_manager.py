import os
import sys
import subprocess
import importlib
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class DependencyInstaller(QThread):
    """依赖安装线程"""
    
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, dependencies: List[str]):
        super().__init__()
        self.dependencies = dependencies
    
    def run(self):
        try:
            total = len(self.dependencies)
            
            for i, dep in enumerate(self.dependencies):
                progress = int((i / total) * 100)
                self.progress.emit(progress, f"正在安装: {dep}")
                
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    self.finished.emit(False, f"安装失败: {dep}\n{result.stderr}")
                    return
            
            self.progress.emit(100, "安装完成")
            self.finished.emit(True, "所有依赖安装成功")
        
        except Exception as e:
            self.finished.emit(False, f"安装失败: {str(e)}")


class DependencyManager:
    """依赖管理器"""
    
    def __init__(self, plugins_dir: str):
        self.plugins_dir = plugins_dir
        self.user_deps_dir = os.path.join(plugins_dir, "_dependencies")
    
    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """获取插件的依赖列表"""
        plugin_json = os.path.join(self.plugins_dir, plugin_name, "plugin.json")
        
        if not os.path.exists(plugin_json):
            return []
        
        try:
            import json
            with open(plugin_json, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("dependencies", [])
        except:
            return []
    
    def check_dependencies(self, plugin_name: str) -> Dict[str, bool]:
        """检查插件依赖是否已安装"""
        dependencies = self.get_plugin_dependencies(plugin_name)
        result = {}
        
        for dep in dependencies:
            package_name = dep.split(">=")[0].split("==")[0].split("<")[0]
            try:
                importlib.import_module(package_name.replace("-", "_"))
                result[dep] = True
            except ImportError:
                result[dep] = False
        
        return result
    
    def install_dependencies(self, plugin_name: str, callback=None) -> bool:
        """安装插件依赖"""
        dependencies = self.get_plugin_dependencies(plugin_name)
        
        if not dependencies:
            return True
        
        for dep in dependencies:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError:
                return False
        
        return True
    
    def install_dependencies_async(self, plugin_name: str, parent=None) -> bool:
        """异步安装插件依赖（带UI）"""
        dependencies = self.get_plugin_dependencies(plugin_name)
        
        if not dependencies:
            return True
        
        dialog = InstallDialog(dependencies, parent)
        return dialog.exec()


class InstallDialog(QDialog):
    """依赖安装对话框"""
    
    def __init__(self, dependencies: List[str], parent=None):
        super().__init__(parent)
        self.dependencies = dependencies
        self.setWindowTitle("安装依赖")
        self.setMinimumSize(450, 300)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("📦 安装插件依赖")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("该插件需要以下依赖包：")
        layout.addWidget(desc)
        
        deps_text = "\n".join([f"• {dep}" for dep in self.dependencies])
        self.deps_label = QLabel(deps_text)
        self.deps_label.setStyleSheet("padding: 10px; background: rgba(255,255,255,0.05); border-radius: 5px;")
        layout.addWidget(self.deps_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备安装...")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.install_btn = QPushButton("安装")
        self.install_btn.setStyleSheet("background-color: #00d4aa; color: white; padding: 8px 20px;")
        self.install_btn.clicked.connect(self._start_install)
        buttons_layout.addWidget(self.install_btn)
        
        layout.addLayout(buttons_layout)
    
    def _start_install(self):
        """开始安装"""
        self.install_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        self.installer = DependencyInstaller(self.dependencies)
        self.installer.progress.connect(self._on_progress)
        self.installer.finished.connect(self._on_finished)
        self.installer.start()
    
    def _on_progress(self, progress: int, message: str):
        """安装进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_finished(self, success: bool, message: str):
        """安装完成"""
        if success:
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: #00d4aa;")
            self.install_btn.setText("完成")
            self.install_btn.setEnabled(True)
            self.install_btn.clicked.disconnect()
            self.install_btn.clicked.connect(self.accept)
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: #ff6b6b;")
            self.install_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
