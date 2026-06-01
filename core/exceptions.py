class ExcelToolsError(Exception):
    """基础异常类"""
    pass


class PluginError(ExcelToolsError):
    """插件相关错误"""
    pass


class FileOperationError(ExcelToolsError):
    """文件操作错误"""
    pass


class ValidationError(ExcelToolsError):
    """数据验证错误"""
    pass


class ConfigurationError(ExcelToolsError):
    """配置错误"""
    pass
