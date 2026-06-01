from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QWidget, QComboBox, QSpinBox,
    QCheckBox, QLineEdit, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QKeySequenceEdit
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        general_tab = QWidget()
        self._setup_general_tab(general_tab)
        tabs.addTab(general_tab, "常规")
        
        shortcuts_tab = QWidget()
        self._setup_shortcuts_tab(shortcuts_tab)
        tabs.addTab(shortcuts_tab, "快捷键")
        
        appearance_tab = QWidget()
        self._setup_appearance_tab(appearance_tab)
        tabs.addTab(appearance_tab, "外观")
        
        advanced_tab = QWidget()
        self._setup_advanced_tab(advanced_tab)
        tabs.addTab(advanced_tab, "高级")
        
        layout.addWidget(tabs)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("background-color: #00d4aa; color: white; padding: 8px 20px;")
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _setup_general_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        startup_group = QGroupBox("启动设置")
        startup_layout = QVBoxLayout()
        
        self.auto_load_check = QCheckBox("启动时自动加载所有插件")
        self.auto_load_check.setChecked(self.config_manager.get("auto_load_plugins", True))
        startup_layout.addWidget(self.auto_load_check)
        
        self.remember_window_check = QCheckBox("记住窗口大小和位置")
        self.remember_window_check.setChecked(self.config_manager.get("remember_window", True))
        startup_layout.addWidget(self.remember_window_check)
        
        self.remember_recent_check = QCheckBox("记住最近使用的功能")
        self.remember_recent_check.setChecked(self.config_manager.get("remember_recent", True))
        startup_layout.addWidget(self.remember_recent_check)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        file_group = QGroupBox("文件设置")
        file_layout = QVBoxLayout()
        
        recent_layout = QHBoxLayout()
        recent_layout.addWidget(QLabel("最近文件数量:"))
        self.recent_count_spin = QSpinBox()
        self.recent_count_spin.setRange(5, 50)
        self.recent_count_spin.setValue(self.config_manager.get("recent_files_count", 10))
        recent_layout.addWidget(self.recent_count_spin)
        file_layout.addLayout(recent_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        layout.addStretch()
    
    def _setup_shortcuts_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        shortcuts_group = QGroupBox("快捷键设置")
        shortcuts_layout = QVBoxLayout()
        
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels(["功能", "快捷键", "操作"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        shortcuts = self.config_manager.get("shortcuts", {
            "open_file": "Ctrl+O",
            "quit": "Ctrl+Q",
            "search": "Ctrl+F",
            "fav_1": "Ctrl+1",
            "fav_2": "Ctrl+2",
            "fav_3": "Ctrl+3",
            "fav_4": "Ctrl+4",
            "fav_5": "Ctrl+5",
        })
        
        shortcut_names = {
            "open_file": "打开文件",
            "quit": "退出程序",
            "search": "搜索功能",
            "fav_1": "收藏功能1",
            "fav_2": "收藏功能2",
            "fav_3": "收藏功能3",
            "fav_4": "收藏功能4",
            "fav_5": "收藏功能5",
        }
        
        self.shortcuts_table.setRowCount(len(shortcuts))
        for i, (key, value) in enumerate(shortcuts.items()):
            self.shortcuts_table.setItem(i, 0, QTableWidgetItem(shortcut_names.get(key, key)))
            shortcut_edit = QKeySequenceEdit(value)
            self.shortcuts_table.setCellWidget(i, 1, shortcut_edit)
            reset_btn = QPushButton("重置")
            reset_btn.clicked.connect(lambda checked, k=key, v=value: self._reset_shortcut(k, v))
            self.shortcuts_table.setCellWidget(i, 2, reset_btn)
        
        shortcuts_layout.addWidget(self.shortcuts_table)
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        layout.addStretch()
    
    def _setup_appearance_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout()
        
        self.dark_mode_check = QCheckBox("深色模式")
        self.dark_mode_check.setChecked(self.config_manager.get("dark_mode", True))
        theme_layout.addWidget(self.dark_mode_check)
        
        accent_layout = QHBoxLayout()
        accent_layout.addWidget(QLabel("强调色:"))
        self.accent_combo = QComboBox()
        self.accent_combo.addItems(["绿色 (#00d4aa)", "蓝色 (#0078d4)", "紫色 (#9c27b0)", "红色 (#f44336)"])
        accent_layout.addWidget(self.accent_combo)
        theme_layout.addLayout(accent_layout)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        layout_group = QGroupBox("布局设置")
        layout_layout = QVBoxLayout()
        
        sidebar_layout = QHBoxLayout()
        sidebar_layout.addWidget(QLabel("侧边栏宽度:"))
        self.sidebar_width_spin = QSpinBox()
        self.sidebar_width_spin.setRange(150, 400)
        self.sidebar_width_spin.setValue(self.config_manager.get("sidebar_width", 220))
        sidebar_layout.addWidget(self.sidebar_width_spin)
        layout_layout.addLayout(sidebar_layout)
        
        layout_group.setLayout(layout_layout)
        layout.addWidget(layout_group)
        
        layout.addStretch()
    
    def _setup_advanced_tab(self, tab):
        layout = QVBoxLayout(tab)
        
        update_group = QGroupBox("更新设置")
        update_layout = QVBoxLayout()
        
        self.auto_update_check = QCheckBox("自动检查更新")
        self.auto_update_check.setChecked(self.config_manager.get("auto_update", True))
        update_layout.addWidget(self.auto_update_check)
        
        self.check_on_start_check = QCheckBox("启动时检查更新")
        self.check_on_start_check.setChecked(self.config_manager.get("check_update_on_start", True))
        update_layout.addWidget(self.check_on_start_check)
        
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)
        
        debug_group = QGroupBox("调试设置")
        debug_layout = QVBoxLayout()
        
        self.debug_mode_check = QCheckBox("调试模式")
        self.debug_mode_check.setChecked(self.config_manager.get("debug_mode", False))
        debug_layout.addWidget(self.debug_mode_check)
        
        self.log_level_layout = QHBoxLayout()
        self.log_level_layout.addWidget(QLabel("日志级别:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.config_manager.get("log_level", "INFO"))
        self.log_level_layout.addWidget(self.log_level_combo)
        debug_layout.addLayout(self.log_level_layout)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
    
    def _reset_shortcut(self, key, value):
        """重置快捷键"""
        row = list(self.config_manager.get("shortcuts", {}).keys()).index(key)
        shortcut_edit = self.shortcuts_table.cellWidget(row, 1)
        shortcut_edit.setKeySequence(value)
    
    def _on_save(self):
        """保存设置"""
        self.config_manager.set("auto_load_plugins", self.auto_load_check.isChecked())
        self.config_manager.set("remember_window", self.remember_window_check.isChecked())
        self.config_manager.set("remember_recent", self.remember_recent_check.isChecked())
        self.config_manager.set("recent_files_count", self.recent_count_spin.value())
        self.config_manager.set("dark_mode", self.dark_mode_check.isChecked())
        self.config_manager.set("sidebar_width", self.sidebar_width_spin.value())
        self.config_manager.set("auto_update", self.auto_update_check.isChecked())
        self.config_manager.set("check_update_on_start", self.check_on_start_check.isChecked())
        self.config_manager.set("debug_mode", self.debug_mode_check.isChecked())
        self.config_manager.set("log_level", self.log_level_combo.currentText())
        
        shortcuts = {}
        for i in range(self.shortcuts_table.rowCount()):
            key = list(self.config_manager.get("shortcuts", {}).keys())[i] if i < len(self.config_manager.get("shortcuts", {})) else f"shortcut_{i}"
            shortcut_edit = self.shortcuts_table.cellWidget(i, 1)
            if shortcut_edit:
                shortcuts[key] = shortcut_edit.keySequence().toString()
        self.config_manager.set("shortcuts", shortcuts)
        
        self.config_manager.save_all()
        self.accept()
