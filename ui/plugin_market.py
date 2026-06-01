import os
import json
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QProgressBar, QTabWidget, QWidget,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class PluginMarket(QDialog):
    """插件市场"""
    
    def __init__(self, plugins_dir: str, parent=None):
        super().__init__(parent)
        self.plugins_dir = plugins_dir
        self.setWindowTitle("插件市场")
        self.setMinimumSize(700, 500)
        self.installed_plugins = self._get_installed_plugins()
        self.available_plugins = self._get_available_plugins()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索插件...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh)
        search_layout.addWidget(refresh_btn)
        layout.addLayout(search_layout)
        
        tabs = QTabWidget()
        
        installed_tab = QWidget()
        self._setup_installed_tab(installed_tab)
        tabs.addTab(installed_tab, f"已安装 ({len(self.installed_plugins)})")
        
        available_tab = QWidget()
        self._setup_available_tab(available_tab)
        tabs.addTab(available_tab, f"可用 ({len(self.available_plugins)})")
        
        layout.addWidget(tabs)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _setup_installed_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        self.installed_table = QTableWidget()
        self.installed_table.setColumnCount(4)
        self.installed_table.setHorizontalHeaderLabels(["名称", "版本", "描述", "操作"])
        self.installed_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.installed_table)
        
        self._update_installed_table()
    
    def _setup_available_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        self.available_table = QTableWidget()
        self.available_table.setColumnCount(5)
        self.available_table.setHorizontalHeaderLabels(["名称", "版本", "描述", "下载量", "操作"])
        self.available_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.available_table)
        
        self._update_available_table()
    
    def _get_installed_plugins(self) -> List[Dict]:
        """获取已安装的插件"""
        plugins = []
        for item in os.listdir(self.plugins_dir):
            plugin_dir = os.path.join(self.plugins_dir, item)
            if os.path.isdir(plugin_dir):
                config_file = os.path.join(plugin_dir, "plugin.json")
                if os.path.exists(config_file):
                    try:
                        with open(config_file, "r", encoding="utf-8") as f:
                            config = json.load(f)
                            plugins.append({
                                "name": config.get("name", item),
                                "version": config.get("version", "1.0.0"),
                                "description": config.get("description", ""),
                                "folder": item
                            })
                    except:
                        pass
        return plugins
    
    def _get_available_plugins(self) -> List[Dict]:
        """获取可用的插件（模拟数据）"""
        return [
            {"name": "Excel转PDF", "version": "1.0.0", "description": "将Excel文件转为PDF格式", "downloads": 1250, "status": "available"},
            {"name": "Word转PDF", "version": "1.0.0", "description": "将Word文档转为PDF格式", "downloads": 980, "status": "available"},
            {"name": "PDF转Word", "version": "1.0.0", "description": "将PDF文档转为Word格式", "downloads": 850, "status": "available"},
            {"name": "图片压缩", "version": "1.0.0", "description": "批量压缩图片文件", "downloads": 720, "status": "available"},
            {"name": "数据可视化", "version": "1.0.0", "description": "生成数据图表", "downloads": 650, "status": "available"},
        ]
    
    def _update_installed_table(self):
        """更新已安装表格"""
        self.installed_table.setRowCount(len(self.installed_plugins))
        for i, plugin in enumerate(self.installed_plugins):
            self.installed_table.setItem(i, 0, QTableWidgetItem(plugin["name"]))
            self.installed_table.setItem(i, 1, QTableWidgetItem(plugin["version"]))
            self.installed_table.setItem(i, 2, QTableWidgetItem(plugin["description"]))
            
            uninstall_btn = QPushButton("卸载")
            uninstall_btn.clicked.connect(lambda checked, f=plugin["folder"]: self._uninstall_plugin(f))
            self.installed_table.setCellWidget(i, 3, uninstall_btn)
    
    def _update_available_table(self):
        """更新可用表格"""
        self.available_table.setRowCount(len(self.available_plugins))
        for i, plugin in enumerate(self.available_plugins):
            self.available_table.setItem(i, 0, QTableWidgetItem(plugin["name"]))
            self.available_table.setItem(i, 1, QTableWidgetItem(plugin["version"]))
            self.available_table.setItem(i, 2, QTableWidgetItem(plugin["description"]))
            self.available_table.setItem(i, 3, QTableWidgetItem(str(plugin["downloads"])))
            
            install_btn = QPushButton("安装")
            install_btn.clicked.connect(lambda checked, n=plugin["name"]: self._install_plugin(n))
            self.available_table.setCellWidget(i, 4, install_btn)
    
    def _on_search(self, text: str):
        """搜索插件"""
        text = text.lower()
        for i in range(self.available_table.rowCount()):
            name = self.available_table.item(i, 0).text().lower()
            desc = self.available_table.item(i, 2).text().lower()
            self.available_table.setRowHidden(i, text not in name and text not in desc)
    
    def _refresh(self):
        """刷新列表"""
        self.installed_plugins = self._get_installed_plugins()
        self.available_plugins = self._get_available_plugins()
        self._update_installed_table()
        self._update_available_table()
        QMessageBox.information(self, "刷新", "插件列表已刷新")
    
    def _install_plugin(self, plugin_name: str):
        """安装插件"""
        QMessageBox.information(self, "安装", f"正在安装插件: {plugin_name}\n\n（模拟安装过程）")
    
    def _uninstall_plugin(self, folder: str):
        """卸载插件"""
        reply = QMessageBox.question(self, "确认卸载", 
            f"确定要卸载插件 '{folder}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "卸载", f"插件 '{folder}' 已卸载")
