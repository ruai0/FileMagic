import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QStatusBar,
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
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


class FileMagicApp(QMainWindow):
    """FileMagic 主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.logger = Logger("FileMagic", os.path.join(self.base_dir, "logs"))
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
        self.setWindowTitle("FileMagic - 全能办公工具集")
        self.setMinimumSize(1200, 600)
        self.resize(1400, 700)
        self.setWindowIcon(self._create_icon("✨"))
    
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
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(240)
        self.sidebar_widget.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setContentsMargins(12, 12, 12, 12)
        self.sidebar_layout.setSpacing(12)

        logo_container = QWidget()
        logo_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                border-radius: 16px;
                padding: 20px;
            }
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_label = QLabel("✨ FileMagic")
        logo_label.setStyleSheet("""
            font-weight: 700; 
            font-size: 20px; 
            color: white;
            letter-spacing: 1px;
        """)
        logo_layout.addWidget(logo_label)
        subtitle_label = QLabel("全能办公工具集")
        subtitle_label.setStyleSheet("""
            font-size: 12px; 
            color: rgba(255,255,255,0.8);
            margin-top: 4px;
        """)
        logo_layout.addWidget(subtitle_label)
        self.sidebar_layout.addWidget(logo_container)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索功能...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px;
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 12px;
                color: #e8e8e8;
                font-size: 13px;
            }
            QLineEdit:focus {
                background: rgba(255,255,255,0.12);
                outline: none;
            }
            QLineEdit::placeholder {
                color: rgba(255,255,255,0.5);
            }
        """)
        self.sidebar_layout.addWidget(self.search_input)

        self.plugin_tree = QTreeWidget()
        self.plugin_tree.setHeaderHidden(True)
        self.plugin_tree.currentItemChanged.connect(self._on_plugin_selected)
        self.plugin_tree.setIndentation(12)
        self.plugin_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: transparent;
                color: #e8e8e8;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px 10px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QTreeWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border-radius: 8px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255,255,255,0.06);
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
                image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
                image: none;
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
                background: rgba(255,255,255,0.05);
                width: 6px;
                border-radius: 3px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.3);
            }
        """)
        self.sidebar_layout.addWidget(scroll_area)

        splitter.addWidget(self.sidebar_widget)

        self.content_widget = QWidget()
        self.content_widget.setObjectName("content")
        self.content_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8fafc, stop:1 #f1f5f9);
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)

        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget { background: transparent; }")
        content_layout.addWidget(self.content_stack)
        
        self.welcome_widget = QWidget()
        self.welcome_widget.setStyleSheet("background: transparent;")
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_layout.setContentsMargins(0, 0, 0, 0)
        welcome_layout.setSpacing(0)
        
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setContentsMargins(0, 40, 0, 0)
        
        self.welcome_title = QLabel("✨ 欢迎使用 FileMagic")
        self.welcome_title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 700; 
            color: #1e293b;
            letter-spacing: -0.5px;
        """)
        self.welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.welcome_title)
        
        self.welcome_desc = QLabel("从左侧选择一个功能开始，或使用搜索快速定位")
        self.welcome_desc.setStyleSheet("""
            font-size: 15px; 
            color: #64748b;
            margin-top: 12px;
        """)
        self.welcome_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.welcome_desc)
        
        welcome_layout.addWidget(header_container)

        self.stats_container = QWidget()
        self.stats_container.setStyleSheet("background: transparent;")
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.setSpacing(24)
        stats_layout.setContentsMargins(0, 50, 0, 0)
        welcome_layout.addWidget(self.stats_container)

        self.shortcuts_widget = QWidget()
        self.shortcuts_widget.setStyleSheet("""
            background: white;
            border-radius: 20px;
            padding: 24px 32px;
            margin-top: 40px;
            border: 1px solid rgba(0,0,0,0.08);
        """)
        shortcuts_layout = QVBoxLayout(self.shortcuts_widget)
        
        self.shortcuts_title = QLabel("⌨️ 快捷键")
        self.shortcuts_title.setStyleSheet("""
            font-weight: 600; 
            font-size: 16px;
            color: #1e293b;
            margin-bottom: 16px;
        """)
        shortcuts_layout.addWidget(self.shortcuts_title)
        
        shortcuts_grid = QGridLayout()
        shortcuts_grid.setSpacing(12)
        
        shortcuts = [
            ("Ctrl+1~9", "快速访问收藏的功能"),
            ("Ctrl+O", "打开文件"),
            ("Ctrl+F", "搜索功能"),
            ("Ctrl+Q", "退出程序")
        ]
        
        for i, (key, desc) in enumerate(shortcuts):
            key_label = QLabel(f"<kbd>{key}</kbd>")
            key_label.setStyleSheet("""
                font-family: 'SF Mono', 'Consolas', monospace;
                font-size: 12px;
                color: #667eea;
                background: rgba(102, 126, 234, 0.1);
                padding: 4px 10px;
                border-radius: 6px;
                font-weight: 500;
            """)
            key_label.setTextFormat(Qt.TextFormat.RichText)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("""
                font-size: 13px;
                color: #64748b;
                padding-left: 12px;
            """)
            
            row_layout = QHBoxLayout()
            row_layout.addWidget(key_label)
            row_layout.addWidget(desc_label)
            row_layout.addStretch()
            
            shortcuts_grid.addLayout(row_layout, i, 0)
        
        shortcuts_layout.addLayout(shortcuts_grid)
        welcome_layout.addWidget(self.shortcuts_widget)
        
        welcome_layout.addStretch()
        
        self.content_stack.addWidget(self.welcome_widget)
        
        splitter.addWidget(self.content_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        self._setup_menu_bar()
        self._setup_status_bar()
    
    def _update_welcome_stats(self):
        """更新欢迎页面的统计信息"""
        plugins = self.plugin_manager.get_all_plugins()
        
        category_counts = {}
        for name, plugin in plugins.items():
            category = getattr(plugin, 'category', '其他')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        categories = [
            ('Excel处理', '📊', '#10b981'),
            ('PDF处理', '📄', '#3b82f6'),
            ('Word处理', '📝', '#f59e0b'),
            ('图片处理', '🖼️', '#ec4899'),
            ('其他', '🔧', '#64748b')
        ]
        
        total_count = sum(category_counts.values())
        
        stats_layout = self.stats_container.layout()
        if stats_layout is None:
            stats_layout = QHBoxLayout(self.stats_container)
            stats_layout.setSpacing(20)
            stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_layout.setContentsMargins(0, 50, 0, 0)
        
        while stats_layout.count():
            child = stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        total_card = QWidget()
        total_card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                border-radius: 16px;
                padding: 20px 32px;
                margin-right: 20px;
            }
        """)
        total_layout = QVBoxLayout(total_card)
        total_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        total_title = QLabel("✨ 总计")
        total_title.setStyleSheet("""
            font-size: 13px;
            color: rgba(255,255,255,0.85);
        """)
        total_layout.addWidget(total_title)
        
        total_count_label = QLabel(f"{total_count}")
        total_count_label.setStyleSheet("""
            font-size: 36px;
            font-weight: 700;
            color: white;
            margin-top: 4px;
        """)
        total_layout.addWidget(total_count_label)
        
        total_subtitle = QLabel("个功能插件")
        total_subtitle.setStyleSheet("""
            font-size: 12px;
            color: rgba(255,255,255,0.7);
        """)
        total_layout.addWidget(total_subtitle)
        
        stats_layout.addWidget(total_card)
        
        for cat_name, emoji, color in categories:
            count = category_counts.get(cat_name, 0)
            if count > 0:
                card = QWidget()
                card.setStyleSheet(f"""
                    QWidget {{
                        background: white;
                        border-radius: 16px;
                        padding: 20px 24px;
                        border: 1px solid rgba(0,0,0,0.08);
                    }}
                    QWidget:hover {{
                        border: 1px solid rgba(102, 126, 234, 0.3);
                        background: rgba(102, 126, 234, 0.02);
                    }}
                """)
                card_layout = QVBoxLayout(card)
                card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                emoji_label = QLabel(emoji)
                emoji_label.setStyleSheet("font-size: 28px;")
                card_layout.addWidget(emoji_label)
                
                count_label = QLabel(f"{count}")
                count_label.setStyleSheet(f"""
                    font-size: 24px;
                    font-weight: 700;
                    color: {color};
                    margin-top: 6px;
                """)
                card_layout.addWidget(count_label)
                
                name_label = QLabel(cat_name)
                name_label.setStyleSheet("""
                    font-size: 12px;
                    color: #64748b;
                    margin-top: 4px;
                """)
                card_layout.addWidget(name_label)
                
                stats_layout.addWidget(card)
    
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
        status_bar.setObjectName("statusBar")
        self.setStatusBar(status_bar)
        status_bar.showMessage("就绪 | 加载中...")
    
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
            
            self._update_welcome_stats()
        
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
        """应用主题样式（深色模式）"""
        sidebar_bg = "#1e1e2e"
        sidebar_hover = "rgba(255,255,255,0.06)"
        accent_start = "#667eea"
        accent_end = "#764ba2"
        text_primary = "#e8e8e8"
        text_secondary = "#a0a0b0"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #0f0f1a;
            }}
            QMenuBar {{
                background-color: #1a1a2e;
                color: {text_primary};
                padding: 8px 12px;
                font-size: 13px;
            }}
            QMenuBar::item {{
                padding: 6px 12px;
                margin: 0 4px;
                border-radius: 6px;
            }}
            QMenuBar::item:selected {{
                background-color: rgba(255,255,255,0.08);
            }}
            QMenu {{
                background-color: #1a1a2e;
                color: {text_primary};
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 140px;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent_start}, stop:1 {accent_end});
                color: white;
            }}
            QStatusBar {{
                background-color: #1a1a2e;
                color: {text_secondary};
                padding: 6px 16px;
                font-size: 12px;
            }}
        """)

        self.sidebar_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {sidebar_bg};
                color: {text_primary};
            }}
        """)

        self.statusBar().showMessage(f"就绪 | {len(self.plugin_manager.get_all_plugins())} 个功能可用")
    
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
