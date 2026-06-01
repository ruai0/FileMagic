from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QComboBox, QCheckBox, QSpinBox,
    QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        theme_group = QGroupBox("外观")
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["系统默认", "亮色", "暗色"])
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        general_layout.addWidget(theme_group)
        
        recent_group = QGroupBox("最近文件")
        recent_layout = QHBoxLayout()
        recent_layout.addWidget(QLabel("显示数量:"))
        self.recent_spin = QSpinBox()
        self.recent_spin.setRange(5, 50)
        self.recent_spin.setValue(10)
        recent_layout.addWidget(self.recent_spin)
        recent_group.setLayout(recent_layout)
        general_layout.addWidget(recent_group)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "通用")
        
        plugin_tab = QWidget()
        plugin_layout = QVBoxLayout(plugin_tab)
        
        self.auto_load_check = QCheckBox("启动时自动加载插件")
        self.auto_load_check.setChecked(True)
        plugin_layout.addWidget(self.auto_load_check)
        
        plugin_layout.addStretch()
        tabs.addTab(plugin_tab, "插件")
        
        layout.addWidget(tabs)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _on_save(self):
        """保存设置"""
        self.accept()
