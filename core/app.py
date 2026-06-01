import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QStatusBar,
    QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QListWidget,
    QListWidgetItem, QStackedWidget, QPushButton,
    QFileDialog, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QMenu, QSystemTrayIcon,
    QApplication, QCheckBox, QScrollArea
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap, QPainter, QColor, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QRect, QPoint

from .plugin_manager import PluginManager
from .config_manager import ConfigManager
from .logger import Logger
from .event_bus import EventBus
from .file_manager import FileManager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.settings import SettingsDialog
from ui.task_manager import TaskManager
from ui.update_checker import UpdateDialog
from ui.plugin_market import PluginMarket
from ui.history import OperationHistory, HistoryWidget
from ui.i18n import I18nManager
from ui.progress_panel import ProgressPanel
from ui.batch_rename import BatchRenamer
from ui.file_preview import FilePreview
from ui.github_market import PluginMarketDialog, UpdateDialog


class ExcelToolsApp(QMainWindow):
    """ExcelTools 主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.logger = Logger("办公工具箱", os.path.join(self.base_dir, "logs"))
        self.config_manager = ConfigManager(os.path.join(self.base_dir, "config"))
        self.event_bus = EventBus()
        self.file_manager = FileManager(self.config_manager)
        self.plugin_manager = PluginManager(
            os.path.join(self.base_dir, "plugins"),
            self.config_manager
        )
        
        self.favorites = self.config_manager.get("favorites", [])
        self.recent_plugins = self.config_manager.get("recent_plugins", [])
        self.dark_mode = False
        
        self.i18n = I18nManager(os.path.join(self.base_dir, "config"))
        self.history = OperationHistory(os.path.join(self.base_dir, "config"))
        
        self.setAcceptDrops(True)
        
        self._setup_window()
        self._setup_ui()
        self._setup_system_tray()
        self._setup_shortcuts()
        self._apply_theme(self.dark_mode)
        self._load_plugins()
        self._load_window_state()
        
        self.logger.info("办公工具箱 启动完成")
    
    def _setup_window(self) -> None:
        """配置主窗口"""
        self.setWindowTitle("办公工具箱 - Excel多功能工具集")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)
        self.setWindowIcon(self._create_icon("📊"))
    
    def _create_icon(self, emoji: str, size: int = 32) -> QIcon:
        """创建emoji图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = painter.font()
        font.setPixelSize(int(size * 0.7))
        painter.setFont(font)
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, emoji)
        painter.end()
        return QIcon(pixmap)
    
    def _setup_ui(self) -> None:
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(220)
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)

        logo_layout = QHBoxLayout()
        logo_label = QLabel("📊 办公工具箱")
        logo_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        logo_layout.addWidget(logo_label)
        self.sidebar_layout.addLayout(logo_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索功能...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                color: #fff;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
            }
        """)
        self.sidebar_layout.addWidget(self.search_input)

        self.plugin_tree = QTreeWidget()
        self.plugin_tree.setHeaderHidden(True)
        self.plugin_tree.currentItemChanged.connect(self._on_plugin_selected)
        self.plugin_tree.setIndentation(15)
        self.plugin_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: transparent;
                color: #e0e0e0;
            }
            QTreeWidget::item {
                padding: 6px 5px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #00d4aa;
                color: #fff;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """)
        self.plugin_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.plugin_tree.customContextMenuRequested.connect(self._on_context_menu)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.plugin_tree)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.3);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.5);
            }
        """)
        self.sidebar_layout.addWidget(scroll_area)

        splitter.addWidget(self.sidebar_widget)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("content")
        self.content_widget.setStyleSheet("background-color: #f5f5f5;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        
        self.welcome_card = QWidget()
        card_layout = QVBoxLayout(self.welcome_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        self.welcome_title = QLabel("欢迎使用 办公工具箱")
        self.welcome_title.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.welcome_title)
        
        self.welcome_desc = QLabel("请从左侧选择一个功能开始使用\n支持右键添加到收藏夹")
        self.welcome_desc.setStyleSheet("font-size: 14px; margin-top: 15px;")
        self.welcome_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.welcome_desc)
        
        features_layout = QHBoxLayout()
        features_layout.setSpacing(20)
        features_layout.setContentsMargins(0, 30, 0, 0)
        
        self.feature_widgets = []
        for emoji, name, desc in [("📁", "Excel处理", "28个功能"), ("📄", "PDF处理", "9个功能"), ("📝", "Word处理", "6个功能")]:
            feature_widget = QWidget()
            feature_layout = QVBoxLayout(feature_widget)
            feature_emoji = QLabel(emoji)
            feature_emoji.setStyleSheet("font-size: 32px;")
            feature_emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
            feature_layout.addWidget(feature_emoji)
            feature_name = QLabel(name)
            feature_name.setStyleSheet("font-weight: bold;")
            feature_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            feature_layout.addWidget(feature_name)
            feature_desc = QLabel(desc)
            feature_desc.setStyleSheet("font-size: 12px;")
            feature_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            feature_layout.addWidget(feature_desc)
            features_layout.addWidget(feature_widget)
            self.feature_widgets.append((feature_widget, feature_name, feature_desc))
        
        card_layout.addLayout(features_layout)
        welcome_layout.addWidget(self.welcome_card)
        
        self.shortcuts_widget = QWidget()
        shortcuts_layout = QVBoxLayout(self.shortcuts_widget)
        self.shortcuts_title = QLabel("⌨️ 快捷键")
        self.shortcuts_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        shortcuts_layout.addWidget(self.shortcuts_title)
        
        self.shortcuts_text = QLabel(
            "Ctrl+1~9: 快速访问收藏的功能\n"
            "Ctrl+O: 打开文件\n"
            "Ctrl+F: 搜索功能\n"
            "Ctrl+Q: 退出程序"
        )
        self.shortcuts_text.setStyleSheet("font-size: 12px; line-height: 1.8;")
        shortcuts_layout.addWidget(self.shortcuts_text)
        welcome_layout.addWidget(self.shortcuts_widget)
        
        self.content_stack.addWidget(self.welcome_widget)
        
        splitter.addWidget(self.content_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        self._setup_menu_bar()
        self._setup_status_bar()
    
    def _setup_menu_bar(self) -> None:
        """设置菜单栏"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d3d;
                color: #e0e0e0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            QMenuBar::item:selected {
                background-color: rgba(255,255,255,0.1);
            }
            QMenu {
                background-color: #2d2d3d;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QMenu::item:selected {
                background-color: #00d4aa;
            }
        """)
        
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = file_menu.addAction("打开(&O)")
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_file)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("退出(&X)")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        
        view_menu = menubar.addMenu("视图(&V)")
        
        favorites_action = view_menu.addAction("收藏夹管理")
        favorites_action.triggered.connect(self._show_favorites_manager)
        
        recent_action = view_menu.addAction("最近使用")
        recent_action.triggered.connect(self._show_recent)
        
        history_action = view_menu.addAction("操作历史")
        history_action.triggered.connect(self._show_history)
        
        view_menu.addSeparator()
        
        task_manager_action = view_menu.addAction("任务管理器")
        task_manager_action.triggered.connect(self._show_task_manager)
        
        progress_action = view_menu.addAction("进度面板")
        progress_action.triggered.connect(self._show_progress_panel)
        
        tools_menu = menubar.addMenu("工具(&T)")
        
        batch_rename_action = tools_menu.addAction("批量重命名")
        batch_rename_action.triggered.connect(self._show_batch_rename)
        
        settings_menu = menubar.addMenu("设置(&S)")
        
        settings_action = settings_menu.addAction("偏好设置(&P)")
        settings_action.triggered.connect(self._show_settings)
        
        language_menu = settings_menu.addMenu("语言")
        for lang in self.i18n.get_available_languages():
            lang_action = language_menu.addAction(self.i18n.get_language_name(lang))
            lang_action.triggered.connect(lambda checked, l=lang: self._change_language(l))
        
        help_menu = menubar.addMenu("帮助(&H)")
        
        plugin_market_action = help_menu.addAction("插件市场(&M)")
        plugin_market_action.triggered.connect(self._show_plugin_market)
        
        update_action = help_menu.addAction("检查更新(&U)")
        update_action.triggered.connect(self._check_update)
        
        help_menu.addSeparator()
        
        about_action = help_menu.addAction("关于(&A)")
        about_action.triggered.connect(self._on_about)
    
    def _setup_status_bar(self) -> None:
        """设置状态栏"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #0f0f23;
                color: #888;
                border-top: 1px solid rgba(255,255,255,0.1);
            }
        """)
        self.setStatusBar(status_bar)
        status_bar.showMessage("就绪 | 28 个功能可用")
    
    def _setup_system_tray(self) -> None:
        """设置系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._create_icon("📊", 64))
        self.tray_icon.setToolTip("办公工具箱 - Excel多功能工具集")
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d3d;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QMenu::item:selected {
                background-color: #00d4aa;
            }
        """)
        
        show_action = tray_menu.addAction("显示窗口")
        show_action.triggered.connect(self._show_window)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _setup_shortcuts(self) -> None:
        """设置快捷键"""
        pass
    
    def _load_plugins(self) -> None:
        """加载插件"""
        try:
            self.plugin_manager.load_all_plugins()
            
            plugins = self.plugin_manager.get_all_plugins()
            categories = {}
            
            for name, plugin in plugins.items():
                plugin.initialize({
                    "config_manager": self.config_manager,
                    "file_manager": self.file_manager,
                    "event_bus": self.event_bus,
                    "logger": self.logger
                })
                
                category = getattr(plugin, 'category', '其他')
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, plugin))
                
                if hasattr(plugin, 'get_widget') and plugin.get_widget():
                    self.content_stack.addWidget(plugin.get_widget())
            
            if self.favorites:
                fav_item = QTreeWidgetItem(self.plugin_tree, ["⭐ 收藏"])
                fav_item.setFlags(fav_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                fav_item.setForeground(0, QColor("#ffd700"))
                for name in self.favorites:
                    if name in plugins:
                        plugin = plugins[name]
                        plugin_item = QTreeWidgetItem(fav_item, [f"  {plugin.name}"])
                        plugin_item.setData(0, Qt.ItemDataRole.UserRole, name)
                        plugin_item.setIcon(0, self._create_icon("⭐"))
                fav_item.setExpanded(True)
            
            if self.recent_plugins:
                recent_item = QTreeWidgetItem(self.plugin_tree, ["🕐 最近使用"])
                recent_item.setFlags(recent_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                recent_item.setForeground(0, QColor("#888"))
                for name in self.recent_plugins[:5]:
                    if name in plugins:
                        plugin = plugins[name]
                        plugin_item = QTreeWidgetItem(recent_item, [f"  {plugin.name}"])
                        plugin_item.setData(0, Qt.ItemDataRole.UserRole, name)
                recent_item.setExpanded(True)
            
            category_order = ['Excel处理', 'PDF处理', 'Word处理', '图片处理', '其他']
            category_emojis = {
                'Excel处理': '📁',
                'PDF处理': '📄',
                'Word处理': '📝',
                '图片处理': '🖼️',
                '其他': '🔧'
            }
            
            for cat in category_order:
                if cat in categories:
                    cat_item = QTreeWidgetItem(self.plugin_tree, [f"{category_emojis.get(cat, '📁')} {cat}"])
                    cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    
                    for name, plugin in sorted(categories[cat], key=lambda x: x[1].name):
                        plugin_item = QTreeWidgetItem(cat_item, [f"  {plugin.name}"])
                        plugin_item.setData(0, Qt.ItemDataRole.UserRole, name)
                    
                    cat_item.setExpanded(True)
            
            self.plugin_tree.expandAll()
            self.logger.info(f"已加载 {len(plugins)} 个插件")
        
        except Exception as e:
            self.logger.error(f"加载插件失败: {str(e)}")
    
    def _on_plugin_selected(self, current, previous) -> None:
        """插件选择事件"""
        if current:
            plugin_name = current.data(0, Qt.ItemDataRole.UserRole)
            if not plugin_name:
                return
            
            plugins = self.plugin_manager.get_all_plugins()
            
            if plugin_name in plugins:
                plugin = plugins[plugin_name]
                widget = plugin.get_widget()
                if widget:
                    index = self.content_stack.indexOf(widget)
                    if index >= 0:
                        self.content_stack.setCurrentIndex(index)
                
                self.statusBar().showMessage(f"当前功能: {plugin.name}")
                
                if plugin_name not in self.recent_plugins:
                    self.recent_plugins.insert(0, plugin_name)
                else:
                    self.recent_plugins.remove(plugin_name)
                    self.recent_plugins.insert(0, plugin_name)
                self.recent_plugins = self.recent_plugins[:10]
                self.config_manager.set("recent_plugins", self.recent_plugins)
    
    def _on_search(self, text: str) -> None:
        """搜索功能"""
        text = text.lower()
        
        for i in range(self.plugin_tree.topLevelItemCount()):
            cat_item = self.plugin_tree.topLevelItem(i)
            has_visible_child = False
            
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                plugin_name = child.data(0, Qt.ItemDataRole.UserRole)
                
                if plugin_name:
                    plugins = self.plugin_manager.get_all_plugins()
                    if plugin_name in plugins:
                        plugin = plugins[plugin_name]
                        match = not text or text in plugin.name.lower() or text in plugin.description.lower()
                        child.setHidden(not match)
                        if match:
                            has_visible_child = True
            
            cat_item.setHidden(not has_visible_child and text != "")
    
    def _on_context_menu(self, pos) -> None:
        """右键菜单"""
        item = self.plugin_tree.itemAt(pos)
        if not item:
            return
        
        plugin_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not plugin_name:
            return
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d3d;
                color: #e0e0e0;
                border: 1px solid rgba(255,255,255,0.1);
            }
            QMenu::item:selected {
                background-color: #00d4aa;
            }
        """)
        
        if plugin_name in self.favorites:
            remove_fav_action = menu.addAction("取消收藏")
            remove_fav_action.triggered.connect(lambda: self._remove_favorite(plugin_name))
        else:
            add_fav_action = menu.addAction("添加到收藏夹")
            add_fav_action.triggered.connect(lambda: self._add_favorite(plugin_name))
        
        menu.addSeparator()
        
        open_action = menu.addAction("打开")
        open_action.triggered.connect(lambda: self._open_plugin(plugin_name))
        
        menu.exec(self.plugin_tree.mapToGlobal(pos))
    
    def _add_favorite(self, plugin_name: str) -> None:
        """添加收藏"""
        if plugin_name not in self.favorites:
            self.favorites.append(plugin_name)
            self.config_manager.set("favorites", self.favorites)
            self._reload_tree()
            self.statusBar().showMessage(f"已添加到收藏夹")
    
    def _remove_favorite(self, plugin_name: str) -> None:
        """取消收藏"""
        if plugin_name in self.favorites:
            self.favorites.remove(plugin_name)
            self.config_manager.set("favorites", self.favorites)
            self._reload_tree()
            self.statusBar().showMessage(f"已取消收藏")
    
    def _reload_tree(self) -> None:
        """重新加载树形菜单"""
        self.plugin_tree.clear()
        self._load_plugins()
    
    def _open_plugin(self, plugin_name: str) -> None:
        """打开插件"""
        plugins = self.plugin_manager.get_all_plugins()
        if plugin_name in plugins:
            plugin = plugins[plugin_name]
            widget = plugin.get_widget()
            if widget:
                index = self.content_stack.indexOf(widget)
                if index >= 0:
                    self.content_stack.setCurrentIndex(index)
    
    def _show_favorites_manager(self) -> None:
        """显示收藏夹管理器"""
        QMessageBox.information(self, "收藏夹管理", 
            f"当前收藏夹中有 {len(self.favorites)} 个功能\n\n"
            "在左侧功能列表上右键点击即可添加/取消收藏")
    
    def _show_recent(self) -> None:
        """显示最近使用"""
        recent_text = "\n".join([f"• {name}" for name in self.recent_plugins[:5]])
        QMessageBox.information(self, "最近使用", 
            f"最近使用的功能：\n\n{recent_text or '暂无'}")
    
    def _apply_theme(self, is_dark: bool) -> None:
        """应用主题样式（仅亮色模式）"""
        bg_primary = "#f5f5f5"
        bg_secondary = "#ffffff"
        bg_tertiary = "#e8e8e8"
        text_primary = "#000000"
        text_secondary = "#444444"
        accent = "#0078d4"
        border = "rgba(0,0,0,0.3)"
        search_bg = "rgba(0,0,0,0.08)"
        search_border = "rgba(0,0,0,0.4)"
        tree_hover = "rgba(0,0,0,0.08)"

        self._theme_colors = {
            "bg_primary": bg_primary,
            "bg_secondary": bg_secondary,
            "bg_tertiary": bg_tertiary,
            "text_primary": text_primary,
            "text_secondary": text_secondary,
            "accent": accent,
            "border": border
        }

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_primary};
            }}
            QMenuBar {{
                background-color: {bg_secondary};
                color: {text_primary};
                border-bottom: 1px solid {border};
            }}
            QMenuBar::item:selected {{
                background-color: {border};
            }}
            QMenu {{
                background-color: {bg_secondary};
                color: {text_primary};
                border: 1px solid {border};
            }}
            QMenu::item:selected {{
                background-color: {accent};
            }}
            QStatusBar {{
                background-color: {bg_tertiary};
                color: {text_secondary};
                border-top: 1px solid {border};
            }}
        """)

        self.sidebar_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_secondary};
                color: {text_primary};
            }}
        """)

        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                background: {search_bg};
                border: 1px solid {search_border};
                border-radius: 6px;
                color: {text_primary};
            }}
            QLineEdit:focus {{
                border-color: {accent};
            }}
        """)

        self.plugin_tree.setStyleSheet(f"""
            QTreeWidget {{
                border: none;
                background-color: transparent;
                color: {text_primary};
            }}
            QTreeWidget::item {{
                padding: 6px 5px;
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {accent};
                color: #fff;
            }}
            QTreeWidget::item:hover {{
                background-color: {tree_hover};
            }}
        """)

        self.content_widget.setStyleSheet(f"background-color: {bg_primary};")

        scroll_area = self.findChild(QScrollArea)
        if scroll_area:
            scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    border: none;
                    background-color: transparent;
                }}
                QScrollBar:vertical {{
                    background: {search_bg};
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background: {search_border};
                    border-radius: 4px;
                    min-height: 30px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {accent};
                }}
            """)
        
        self.welcome_card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #f5f5f5);
                border-radius: 15px;
                border: 1px solid rgba(0,0,0,0.3);
            }}
        """)
        self.welcome_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: #000000;")
        self.welcome_desc.setStyleSheet(f"font-size: 14px; color: #444444; margin-top: 15px;")
        
        for feature_widget, feature_name, feature_desc in self.feature_widgets:
            feature_widget.setStyleSheet(f"""
                QWidget {{
                    background: rgba(0,0,0,0.05);
                    border-radius: 10px;
                    padding: 15px;
                }}
                QWidget:hover {{
                    background: rgba(0,120,212,0.15);
                    border: 1px solid #0078d4;
                }}
            """)
            feature_name.setStyleSheet(f"font-weight: bold; color: #000000;")
            feature_desc.setStyleSheet(f"font-size: 12px; color: #444444;")
        
        self.shortcuts_widget.setStyleSheet(f"""
            QWidget {{
                background: rgba(0,0,0,0.03);
                border-radius: 10px;
                margin-top: 20px;
            }}
        """)
        self.shortcuts_title.setStyleSheet(f"font-weight: bold; color: #000000; margin-bottom: 10px;")
        self.shortcuts_text.setStyleSheet(f"font-size: 12px; color: #444444; line-height: 1.8;")
    
    def _on_open_file(self) -> None:
        """打开文件"""
        filepaths, _ = QFileDialog.getOpenFileNames(
            self,
            "打开Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls *.xlsm *.xlsb);;CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if filepaths:
            for filepath in filepaths:
                self.file_manager.add_recent_file(filepath)
            self.statusBar().showMessage(f"已打开 {len(filepaths)} 个文件")
    
    def _on_about(self) -> None:
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于 办公工具箱",
            "办公工具箱 v1.0.0\n\n"
            "Excel多功能工具集\n"
            "基于 Python + PyQt6 开发\n\n"
            "支持功能:\n"
            "- 文件合并/拆分\n"
            "- 数据清洗/分析\n"
            "- PDF处理\n"
            "- Word处理\n"
            "- 图片处理"
        )
    
    def _on_tray_activated(self, reason) -> None:
        """托盘图标点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()
    
    def _show_window(self) -> None:
        """显示窗口"""
        self.showNormal()
        self.activateWindow()
    
    def _quit_app(self) -> None:
        """退出应用"""
        self.config_manager.save_all()
        QApplication.quit()
    
    def _load_window_state(self) -> None:
        """加载窗口状态"""
        geometry = self.config_manager.get("window_geometry")
        if geometry:
            self.setGeometry(
                geometry.get("x", 100),
                geometry.get("y", 100),
                geometry.get("width", 1400),
                geometry.get("height", 700)
            )
        
        if self.config_manager.get("window_maximized", False):
            self.showMaximized()
    
    def _save_window_state(self) -> None:
        """保存窗口状态"""
        geometry = self.geometry()
        self.config_manager.set("window_geometry", {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height()
        })
        self.config_manager.set("window_maximized", self.isMaximized())
    
    def _show_settings(self) -> None:
        """显示设置对话框"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            self.dark_mode = self.config_manager.get("dark_mode", True)
            self._apply_theme(self.dark_mode)
            self.statusBar().showMessage("设置已保存")
    
    def _show_task_manager(self) -> None:
        """显示任务管理器"""
        if not hasattr(self, '_task_manager_window'):
            self._task_manager_window = TaskManager()
        self._task_manager_window.show()
        self._task_manager_window.activateWindow()
    
    def _show_history(self) -> None:
        """显示操作历史"""
        if not hasattr(self, '_history_window'):
            self._history_window = HistoryWidget(self.history)
        self._history_window.show()
        self._history_window.activateWindow()
        self._history_window.refresh()
    
    def _show_progress_panel(self) -> None:
        """显示进度面板"""
        if not hasattr(self, '_progress_window'):
            self._progress_window = ProgressPanel()
        self._progress_window.show()
        self._progress_window.activateWindow()
    
    def _show_batch_rename(self) -> None:
        """显示批量重命名"""
        if not hasattr(self, '_batch_rename_window'):
            self._batch_rename_window = BatchRenamer()
        self._batch_rename_window.show()
        self._batch_rename_window.activateWindow()
    
    def _show_plugin_market(self) -> None:
        """显示插件市场"""
        dialog = PluginMarketDialog(
            os.path.join(self.base_dir, "plugins"),
            self
        )
        dialog.exec()
    
    def _change_language(self, language: str) -> None:
        """切换语言"""
        self.i18n.set_language(language)
        self.config_manager.set("language", language)
        self.statusBar().showMessage(f"语言已切换为: {self.i18n.get_language_name(language)}")
    
    def _check_update(self) -> None:
        """检查更新"""
        dialog = UpdateDialog("1.0.0", self)
        dialog.exec()
    
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent) -> None:
        """拖放事件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            for file in files:
                self.file_manager.add_recent_file(file)
            self.statusBar().showMessage(f"已添加 {len(files)} 个文件")
    
    def closeEvent(self, event) -> None:
        """窗口关闭事件"""
        self._save_window_state()
        self.config_manager.save_all()
        self.logger.info("办公工具箱 已退出")
        event.accept()
    
    def changeEvent(self, event) -> None:
        """窗口状态改变事件"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized():
                self.hide()
                self.tray_icon.showMessage(
                    "办公工具箱",
                    "程序已最小化到系统托盘",
                    QSystemTrayIcon.MessageIcon.Information,
                    1000
                )
