class FileMagicError(Exception):
    """基础异常类"""
    pass


class PluginError(FileMagicError):
    """插件相关错误"""
    pass


class FileOperationError(FileMagicError):
    """文件操作错误"""
    pass


class ValidationError(FileMagicError):
    """数据验证错误"""
    pass


class ConfigurationError(FileMagicError):
    """配置错误"""
    pass
