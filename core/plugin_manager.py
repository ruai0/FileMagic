import os
import sys
import importlib
import json
import subprocess
from typing import Dict, List, Optional, Any
from .exceptions import PluginError


class BasePlugin:
    """插件基类"""
    
    def __init__(self):
        self.name = "未命名插件"
        self.description = "插件描述"
        self.version = "1.0.0"
        self.author = "未知"
        self.category = "其他"
        self.enabled = True
        self.dependencies = []
        self._context: Optional[Dict[str, Any]] = None
    
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        self._context = context
    
    def activate(self) -> None:
        """激活插件"""
        self.enabled = True
    
    def deactivate(self) -> None:
        """停用插件"""
        self.enabled = False
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """返回插件的菜单项"""
        return []
    
    def get_toolbar_items(self) -> List[Dict[str, str]]:
        """返回插件的工具栏项"""
        return []
    
    def get_widget(self):
        """返回插件的主界面组件"""
        return None


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str = "plugins", config_manager=None):
        self.plugins_dir = plugins_dir
        self.config_manager = config_manager
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        discovered = []
        
        for item in os.listdir(self.plugins_dir):
            plugin_dir = os.path.join(self.plugins_dir, item)
            if os.path.isdir(plugin_dir):
                plugin_json = os.path.join(plugin_dir, "plugin.json")
                plugin_py = os.path.join(plugin_dir, "plugin.py")
                
                if os.path.exists(plugin_json) and os.path.exists(plugin_py):
                    discovered.append(item)
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """加载插件"""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
        
        plugin_dir = os.path.join(self.plugins_dir, plugin_name)
        plugin_json = os.path.join(plugin_dir, "plugin.json")
        plugin_py = os.path.join(plugin_dir, "plugin.py")
        
        if not os.path.exists(plugin_json) or not os.path.exists(plugin_py):
            raise PluginError(f"插件文件不完整: {plugin_name}")
        
        try:
            with open(plugin_json, "r", encoding="utf-8") as f:
                self.plugin_configs[plugin_name] = json.load(f)
        except json.JSONDecodeError:
            raise PluginError(f"插件配置文件格式错误: {plugin_name}")
        
        dependencies = self.plugin_configs[plugin_name].get("dependencies", [])
        if dependencies:
            self._check_and_install_dependencies(plugin_name, dependencies)
        
        try:
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)
            
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}.plugin",
                plugin_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "Plugin"):
                plugin_instance = module.Plugin()
                if "category" in self.plugin_configs.get(plugin_name, {}):
                    plugin_instance.category = self.plugin_configs[plugin_name]["category"]
                plugin_instance.dependencies = dependencies
                self.plugins[plugin_name] = plugin_instance
                return plugin_instance
            else:
                raise PluginError(f"插件未找到 Plugin 类: {plugin_name}")
        
        except Exception as e:
            raise PluginError(f"加载插件失败 {plugin_name}: {str(e)}")
    
    def _check_and_install_dependencies(self, plugin_name: str, dependencies: List[str]) -> None:
        """检查并安装插件依赖"""
        missing = []
        
        for dep in dependencies:
            package_name = dep.split(">=")[0].split("==")[0].split("<")[0].replace("-", "_")
            try:
                importlib.import_module(package_name)
            except ImportError:
                missing.append(dep)
        
        if missing:
            print(f"插件 {plugin_name} 需要安装以下依赖: {', '.join(missing)}")
            for dep in missing:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep],
                        capture_output=True,
                        check=True
                    )
                    print(f"已安装: {dep}")
                except subprocess.CalledProcessError:
                    print(f"安装失败: {dep}")
    
    def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.deactivate()
            del self.plugins[plugin_name]
    
    def activate_plugin(self, plugin_name: str) -> None:
        """激活插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].activate()
    
    def deactivate_plugin(self, plugin_name: str) -> None:
        """停用插件"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].deactivate()
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已加载的插件"""
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> List[str]:
        """获取启用的插件列表"""
        enabled = []
        if self.config_manager:
            enabled = self.config_manager.get("plugins.enabled", [])
        return enabled
    
    def load_all_plugins(self) -> None:
        """加载所有可用插件"""
        discovered = self.discover_plugins()
        enabled = self.get_enabled_plugins()
        
        for plugin_name in discovered:
            if enabled == ["*"] or plugin_name in enabled:
                try:
                    self.load_plugin(plugin_name)
                except PluginError as e:
                    print(f"警告: {e}")
