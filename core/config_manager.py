import json
import os
from typing import Any, Dict, Optional
from .exceptions import ConfigurationError


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.configs: Dict[str, Any] = {}
        self._observers: list = []
        
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        self.load_all_configs()
    
    def load_all_configs(self) -> None:
        """加载所有配置文件"""
        self._load_config("app_config", "app_config.json")
        self._load_config("plugins", "plugins.json")
        self._load_config("shortcuts", "shortcuts.json")
    
    def _load_config(self, name: str, filename: str) -> None:
        """加载单个配置文件"""
        filepath = os.path.join(self.config_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.configs[name] = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"配置文件格式错误: {filename}")
        else:
            self.configs[name] = self._get_default_config(name)
            self._save_config(name, filename)
    
    def _get_default_config(self, name: str) -> Dict[str, Any]:
        """获取默认配置"""
        defaults = {
            "app_config": {
                "app": {
                    "name": "ExcelTools",
                    "version": "1.0.0",
                    "language": "zh-CN",
                    "theme": "system"
                },
                "general": {
                    "auto_save": True,
                    "auto_save_interval": 300,
                    "recent_files_count": 10,
                    "default_encoding": "utf-8"
                },
                "interface": {
                    "dpi_aware": True,
                    "toolbar_style": "icon_and_text",
                    "sidebar_position": "left",
                    "status_bar_visible": True
                },
                "plugins": {
                    "auto_load": True,
                    "enabled_plugins": ["*"],
                    "disabled_plugins": []
                },
                "advanced": {
                    "log_level": "INFO",
                    "log_file": "logs/app.log",
                    "backup_enabled": True,
                    "backup_dir": "backups"
                }
            },
            "plugins": {
                "enabled": ["file_merger", "file_splitter", "data_cleaner", "format_converter", "data_analyzer", "batch_processor"],
                "disabled": []
            },
            "shortcuts": {}
        }
        return defaults.get(name, {})
    
    def _save_config(self, name: str, filename: str) -> None:
        """保存配置文件"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.configs[name], f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ConfigurationError(f"保存配置文件失败: {filename}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        keys = key.split(".")
        value = self.configs
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的路径"""
        keys = key.split(".")
        config = self.configs
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._notify_observers(key, value)
    
    def save(self, config_name: str) -> None:
        """保存指定配置"""
        filename = f"{config_name}.json"
        self._save_config(config_name, filename)
    
    def save_all(self) -> None:
        """保存所有配置"""
        for name in self.configs:
            self.save(name)
    
    def add_observer(self, observer) -> None:
        """添加配置变更观察者"""
        self._observers.append(observer)
    
    def _notify_observers(self, key: str, value: Any) -> None:
        """通知观察者配置变更"""
        for observer in self._observers:
            try:
                observer(key, value)
            except Exception:
                pass
