"""
PDF转图片工具 v1.1
功能完整的PDF转图片桌面应用

功能特性:
- PDF转PNG/JPG/BMP/TIFF
- 批量处理（多线程并发）
- 文字/图片水印
- 图片裁剪
- 图片合并为PDF
- OCR文字识别

技术栈: Python + PyQt6 + PyMuPDF
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QFontDatabase

from ui.main_window import MainWindow
from utils.config import ConfigManager
from utils.logger import get_logger


VERSION = "1.1"


def create_splash_screen():
    """创建启动画面"""
    # 创建启动画面图片
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor("#1e1e1e"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("#007acc"))
    painter.setFont(QFont("Microsoft YaHei", 24, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📄 PDF转图片工具")
    painter.setPen(QColor("#d4d4d4"))
    painter.setFont(QFont("Microsoft YaHei", 12))
    painter.drawText(pixmap.rect().adjusted(0, 80, 0, 0), Qt.AlignmentFlag.AlignCenter, f"版本 {VERSION}")
    painter.drawText(pixmap.rect().adjusted(0, 120, 0, 0), Qt.AlignmentFlag.AlignCenter, "正在加载...")
    painter.end()

    return QSplashScreen(pixmap)


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("PDF转图片工具")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("PDFConverter")
    app.setOrganizationDomain("pdfconverter.local")

    # 设置高DPI支持
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 显示启动画面
    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    # 初始化配置
    config = ConfigManager()

    # 初始化日志
    logger = get_logger()
    logger.info(f"应用启动 - 版本 {VERSION}")

    # 设置字体
    font = QFont()
    font.setPointSize(config.get("font_size", 10))
    font.setFamily("Microsoft YaHei")
    app.setFont(font)

    # 创建主窗口
    window = MainWindow(config)

    # 延迟关闭启动画面并显示主窗口
    def show_main_window():
        splash.finish(window)
        window.show()

    QTimer.singleShot(1000, show_main_window)

    # 运行应用
    exit_code = app.exec()

    logger.info("应用退出")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
