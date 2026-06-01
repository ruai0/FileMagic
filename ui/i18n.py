import os
import json
from typing import Dict, Optional
from PyQt6.QtCore import QObject, QTranslator, QCoreApplication


class I18nManager:
    """国际化管理器"""
    
    def __init__(self, config_dir: str):
        self.config_dir = config_dir
        self.translations_dir = os.path.join(config_dir, "translations")
        self.current_language = "zh_CN"
        self.translations: Dict[str, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self):
        """加载翻译文件"""
        if not os.path.exists(self.translations_dir):
            os.makedirs(self.translations_dir)
            self._create_default_translations()
        
        for filename in os.listdir(self.translations_dir):
            if filename.endswith(".json"):
                lang = filename[:-5]
                filepath = os.path.join(self.translations_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                except:
                    pass
    
    def _create_default_translations(self):
        """创建默认翻译文件"""
        zh_cn = {
            "app_name": "办公工具箱",
            "menu_file": "文件",
            "menu_view": "视图",
            "menu_settings": "设置",
            "menu_help": "帮助",
            "action_open": "打开",
            "action_quit": "退出",
            "action_settings": "偏好设置",
            "action_update": "检查更新",
            "action_about": "关于",
            "action_favorites": "收藏夹管理",
            "action_recent": "最近使用",
            "action_task_manager": "任务管理器",
            "action_history": "操作历史",
            "status_ready": "就绪",
            "status_loading": "加载中...",
            "theme_dark": "深色模式",
            "theme_light": "亮色模式",
            "shortcut_search": "搜索功能",
            "plugin_install": "安装",
            "plugin_uninstall": "卸载",
            "plugin_market": "插件市场"
        }
        
        en_us = {
            "app_name": "Office Toolbox",
            "menu_file": "File",
            "menu_view": "View",
            "menu_settings": "Settings",
            "menu_help": "Help",
            "action_open": "Open",
            "action_quit": "Quit",
            "action_settings": "Preferences",
            "action_update": "Check for Updates",
            "action_about": "About",
            "action_favorites": "Favorites Manager",
            "action_recent": "Recent",
            "action_task_manager": "Task Manager",
            "action_history": "Operation History",
            "status_ready": "Ready",
            "status_loading": "Loading...",
            "theme_dark": "Dark Mode",
            "theme_light": "Light Mode",
            "shortcut_search": "Search",
            "plugin_install": "Install",
            "plugin_uninstall": "Uninstall",
            "plugin_market": "Plugin Market"
        }
        
        with open(os.path.join(self.translations_dir, "zh_CN.json"), "w", encoding="utf-8") as f:
            json.dump(zh_cn, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.translations_dir, "en_US.json"), "w", encoding="utf-8") as f:
            json.dump(en_us, f, ensure_ascii=False, indent=2)
    
    def set_language(self, language: str):
        """设置语言"""
        if language in self.translations:
            self.current_language = language
    
    def translate(self, key: str, default: str = None) -> str:
        """翻译文本"""
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, default or key)
        return default or key
    
    def get_available_languages(self) -> list:
        """获取可用语言列表"""
        return ["zh_CN", "en_US"]
    
    def get_language_name(self, lang_code: str) -> str:
        """获取语言名称"""
        names = {
            "zh_CN": "简体中文",
            "en_US": "English"
        }
        return names.get(lang_code, lang_code)
