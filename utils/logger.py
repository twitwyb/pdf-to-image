"""
日志工具模块
"""
import os
import logging
from datetime import datetime
from typing import Optional


class AppLogger:
    """应用日志器"""

    def __init__(self, log_dir: Optional[str] = None, name: str = "PDFConverter"):
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(os.path.expanduser("~"), ".pdf_converter", "logs")

        os.makedirs(self.log_dir, exist_ok=True)

        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 文件处理器
        log_file = os.path.join(
            self.log_dir,
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)

    def exception(self, message: str):
        """异常日志（包含堆栈信息）"""
        self.logger.exception(message)


# 全局日志器实例
_logger: Optional[AppLogger] = None


def get_logger() -> AppLogger:
    """获取全局日志器"""
    global _logger
    if _logger is None:
        _logger = AppLogger()
    return _logger
