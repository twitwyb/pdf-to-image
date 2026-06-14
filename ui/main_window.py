"""
主窗口模块 - 优化版
支持拖拽、最近文件、设置对话框等
"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QApplication, QDialog, QFormLayout,
    QSpinBox, QCheckBox, QDialogButtonBox, QComboBox
)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QAction, QIcon, QFont, QDragEnterEvent, QDropEvent

from .convert_tab import ConvertTab
from .batch_tab import BatchTab
from .edit_tab import EditTab
from .ocr_tab import OCRTab
from utils.config import ConfigManager
from utils.logger import get_logger
from utils.file_utils import is_pdf_file, is_image_file


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QFormLayout(self)

        # 默认DPI
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(self.config.get("default_dpi", 300))
        layout.addRow("默认DPI:", self.dpi_spin)

        # 默认格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP", "TIFF"])
        self.format_combo.setCurrentText(self.config.get("default_format", "PNG").upper())
        layout.addRow("默认格式:", self.format_combo)

        # 默认质量
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(self.config.get("default_quality", 95))
        self.quality_spin.setSuffix("%")
        layout.addRow("JPG质量:", self.quality_spin)

        # 并发线程数
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(self.config.get("max_workers", 4))
        layout.addRow("批量处理线程数:", self.workers_spin)

        # 字体大小
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 16)
        self.font_spin.setValue(self.config.get("font_size", 10))
        layout.addRow("界面字体大小:", self.font_spin)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def save_settings(self):
        """保存设置"""
        self.config.set("default_dpi", self.dpi_spin.value())
        self.config.set("default_format", self.format_combo.currentText().lower())
        self.config.set("default_quality", self.quality_spin.value())
        self.config.set("max_workers", self.workers_spin.value())
        self.config.set("font_size", self.font_spin.value())
        self.accept()


class MainWindow(QMainWindow):
    """主窗口 - 支持拖拽和最近文件"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.logger = get_logger()

        self.init_ui()
        self.restore_geometry()

        # 启用拖拽
        self.setAcceptDrops(True)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("PDF转图片工具 v1.1")
        self.setMinimumSize(1000, 700)
        self.resize(
            self.config.get("window_width", 1200),
            self.config.get("window_height", 800)
        )

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # 添加标签页
        self.convert_tab = ConvertTab(self.config)
        self.batch_tab = BatchTab(self.config)
        self.edit_tab = EditTab(self.config)
        self.ocr_tab = OCRTab(self.config)

        self.tab_widget.addTab(self.convert_tab, "📄 PDF转图片")
        self.tab_widget.addTab(self.batch_tab, "📚 批量处理")
        self.tab_widget.addTab(self.edit_tab, "✏️ 编辑功能")
        self.tab_widget.addTab(self.ocr_tab, "🔍 OCR识别")

        # 标签页切换时更新状态
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.tab_widget)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏
        self.create_status_bar()

        # 设置样式
        self.setStyleSheet(self.get_stylesheet())

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        open_action = QAction("打开PDF文件(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        open_dir_action = QAction("打开文件夹(&D)", self)
        open_dir_action.setShortcut("Ctrl+Shift+O")
        open_dir_action.triggered.connect(self.open_directory)
        file_menu.addAction(open_dir_action)

        # 最近文件子菜单
        self.recent_menu = file_menu.addMenu("最近文件(&R)")
        self.update_recent_menu()

        file_menu.addSeparator()

        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")

        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        theme_menu = view_menu.addMenu("主题(&T)")

        light_theme = QAction("浅色主题", self)
        light_theme.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme)

        dark_theme = QAction("深色主题", self)
        dark_theme.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme)

        view_menu.addSeparator()

        # 快捷键说明
        shortcuts_action = QAction("快捷键说明(&K)", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        view_menu.addAction(shortcuts_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")

        help_action = QAction("使用帮助(&H)", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("就绪 | 拖拽PDF或图片文件到窗口可快速打开")
        self.status_bar.addWidget(self.status_label)

        # 版本信息
        version_label = QLabel("v1.1")
        self.status_bar.addPermanentWidget(version_label)

    def update_recent_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        recent_files = self.config.get_recent_files()

        if not recent_files:
            no_recent = QAction("无最近文件", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
        else:
            for file_path in recent_files[:10]:
                action = QAction(os.path.basename(file_path), self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
                self.recent_menu.addAction(action)

            self.recent_menu.addSeparator()
            clear_action = QAction("清除记录", self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)

    def open_recent_file(self, file_path: str):
        """打开最近文件"""
        if os.path.exists(file_path):
            if is_pdf_file(file_path):
                self.tab_widget.setCurrentWidget(self.convert_tab)
                self.convert_tab.load_files([file_path])
            elif is_image_file(file_path):
                self.tab_widget.setCurrentWidget(self.edit_tab)
                self.edit_tab.load_files([file_path])
        else:
            QMessageBox.warning(self, "文件不存在", f"文件不存在: {file_path}")

    def clear_recent_files(self):
        """清除最近文件记录"""
        recent_file = os.path.join(self.config.config_dir, "recent.json")
        if os.path.exists(recent_file):
            os.remove(recent_file)
        self.update_recent_menu()

    def on_tab_changed(self, index):
        """标签页切换"""
        tab_names = ["PDF转图片", "批量处理", "编辑功能", "OCR识别"]
        if 0 <= index < len(tab_names):
            self.status_label.setText(f"当前功能: {tab_names[index]}")

    def open_file(self):
        """打开PDF文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )

        if file_paths:
            self.load_files(file_paths)

    def load_files(self, file_paths: list):
        """加载文件"""
        pdf_files = [f for f in file_paths if is_pdf_file(f)]
        image_files = [f for f in file_paths if is_image_file(f)]

        if pdf_files:
            self.tab_widget.setCurrentWidget(self.convert_tab)
            self.convert_tab.load_files(pdf_files)
            for path in pdf_files:
                self.config.add_recent_file(path)

        if image_files:
            if not pdf_files:
                self.tab_widget.setCurrentWidget(self.edit_tab)
            self.edit_tab.load_files(image_files)

        self.update_recent_menu()
        self.status_label.setText(f"已加载 {len(file_paths)} 个文件")

    def open_directory(self):
        """打开文件夹"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if dir_path:
            self.tab_widget.setCurrentWidget(self.batch_tab)
            self.batch_tab.load_directory(dir_path)
            self.status_label.setText(f"已加载文件夹: {dir_path}")

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "设置", "设置已保存，部分设置需要重启程序生效。")

    def set_theme(self, theme: str):
        """设置主题"""
        self.config.set("theme", theme)
        self.setStyleSheet(self.get_stylesheet())
        self.status_label.setText(f"已切换到{'深色' if theme == 'dark' else '浅色'}主题")

    def show_shortcuts(self):
        """显示快捷键说明"""
        QMessageBox.information(
            self,
            "快捷键说明",
            "<h3>快捷键列表</h3>"
            "<table>"
            "<tr><td><b>Ctrl+O</b></td><td>打开PDF文件</td></tr>"
            "<tr><td><b>Ctrl+Shift+O</b></td><td>打开文件夹</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>打开设置</td></tr>"
            "<tr><td><b>Ctrl+Q</b></td><td>退出程序</td></tr>"
            "<tr><td><b>F1</b></td><td>使用帮助</td></tr>"
            "</table>"
            "<p>拖拽文件到窗口可快速打开</p>"
        )

    def show_help(self):
        """显示使用帮助"""
        QMessageBox.information(
            self,
            "使用帮助",
            "<h2>PDF转图片工具 - 使用帮助</h2>"
            "<h3>📄 PDF转图片</h3>"
            "<p>1. 点击「添加文件」或拖拽PDF文件到窗口</p>"
            "<p>2. 设置输出格式、DPI、页面范围</p>"
            "<p>3. 选择输出目录</p>"
            "<p>4. 点击「开始转换」</p>"
            "<h3>📚 批量处理</h3>"
            "<p>1. 添加多个PDF文件或整个文件夹</p>"
            "<p>2. 统一设置输出参数</p>"
            "<p>3. 点击「开始批量处理」</p>"
            "<h3>✏️ 编辑功能</h3>"
            "<p><b>水印:</b> 支持文字和图片水印，可设置位置、透明度</p>"
            "<p><b>裁剪:</b> 按比例、居中或百分比裁剪</p>"
            "<p><b>合并:</b> 多图合并为PDF或拼接</p>"
            "<h3>🔍 OCR识别</h3>"
            "<p>需要安装Tesseract OCR引擎</p>"
            "<p>支持中英文识别，可导出TXT/Word</p>"
        )

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 PDF转图片工具",
            "<h2>📄 PDF转图片工具</h2>"
            "<p><b>版本:</b> 1.1</p>"
            "<p><b>作者:</b> PDF Converter Team</p>"
            "<hr>"
            "<p>一个功能强大的PDF转图片桌面工具，支持：</p>"
            "<ul>"
            "<li>✅ PDF转PNG/JPG/BMP/TIFF</li>"
            "<li>✅ 批量处理（多线程并发）</li>"
            "<li>✅ 添加文字/图片水印</li>"
            "<li>✅ 图片裁剪（按比例/居中/百分比）</li>"
            "<li>✅ 图片合并为PDF/拼接</li>"
            "<li>✅ OCR文字识别（中英文）</li>"
            "</ul>"
            "<hr>"
            "<p><b>技术栈:</b> Python + PyQt6 + PyMuPDF</p>"
            "<p><b>开源协议:</b> MIT License</p>"
        )

    def get_stylesheet(self) -> str:
        """获取样式表"""
        theme = self.config.get("theme", "light")

        if theme == "dark":
            return """
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QTabWidget::pane {
                    border: 1px solid #3c3c3c;
                    background-color: #252526;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #969696;
                    padding: 10px 20px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    font-size: 13px;
                }
                QTabBar::tab:selected {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border-bottom: 2px solid #007acc;
                }
                QTabBar::tab:hover {
                    background-color: #383838;
                }
                QPushButton {
                    background-color: #007acc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1a8cff;
                }
                QPushButton:pressed {
                    background-color: #005c99;
                }
                QPushButton:disabled {
                    background-color: #3c3c3c;
                    color: #666666;
                }
                QLineEdit, QSpinBox, QComboBox {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 3px;
                }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border: 1px solid #007acc;
                }
                QGroupBox {
                    border: 1px solid #3c3c3c;
                    border-radius: 4px;
                    margin-top: 12px;
                    padding-top: 18px;
                    font-weight: bold;
                    color: #d4d4d4;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QProgressBar {
                    border: 1px solid #3c3c3c;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #2d2d2d;
                }
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 2px;
                }
                QTableWidget {
                    border: 1px solid #3c3c3c;
                    gridline-color: #3c3c3c;
                    background-color: #252526;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QTableWidget::item:selected {
                    background-color: #007acc;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    border: none;
                    border-right: 1px solid #3c3c3c;
                    border-bottom: 1px solid #3c3c3c;
                    padding: 8px;
                    font-weight: bold;
                    color: #d4d4d4;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                }
                QMenuBar::item:selected {
                    background-color: #383838;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QMenu::item:selected {
                    background-color: #007acc;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: white;
                }
                QCheckBox {
                    color: #d4d4d4;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QRadioButton {
                    color: #d4d4d4;
                    spacing: 8px;
                }
                QLabel {
                    color: #d4d4d4;
                }
                QTextEdit {
                    background-color: #252526;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QSlider::groove:horizontal {
                    height: 6px;
                    background: #3c3c3c;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    background: #007acc;
                    border-radius: 8px;
                }
            """
        else:
            return """
                QMainWindow, QWidget {
                    background-color: #f8f9fa;
                    color: #333333;
                }
                QTabWidget::pane {
                    border: 1px solid #dee2e6;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #e9ecef;
                    color: #6c757d;
                    padding: 10px 20px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    font-size: 13px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    color: #333333;
                    border-bottom: 2px solid #007acc;
                }
                QTabBar::tab:hover {
                    background-color: #dee2e6;
                }
                QPushButton {
                    background-color: #007acc;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1a8cff;
                }
                QPushButton:pressed {
                    background-color: #005c99;
                }
                QPushButton:disabled {
                    background-color: #e9ecef;
                    color: #adb5bd;
                }
                QLineEdit, QSpinBox, QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #ced4da;
                    padding: 6px;
                    border-radius: 3px;
                }
                QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                    border: 1px solid #007acc;
                }
                QGroupBox {
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    margin-top: 12px;
                    padding-top: 18px;
                    font-weight: bold;
                    color: #333333;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QProgressBar {
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #e9ecef;
                }
                QProgressBar::chunk {
                    background-color: #007acc;
                    border-radius: 2px;
                }
                QTableWidget {
                    border: 1px solid #dee2e6;
                    gridline-color: #e9ecef;
                    background-color: #ffffff;
                }
                QTableWidget::item {
                    padding: 5px;
                }
                QTableWidget::item:selected {
                    background-color: #007acc;
                    color: white;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    border: none;
                    border-right: 1px solid #dee2e6;
                    border-bottom: 1px solid #dee2e6;
                    padding: 8px;
                    font-weight: bold;
                    color: #495057;
                }
                QMenuBar {
                    background-color: #ffffff;
                    color: #333333;
                    border-bottom: 1px solid #dee2e6;
                }
                QMenuBar::item:selected {
                    background-color: #e9ecef;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #dee2e6;
                }
                QMenu::item:selected {
                    background-color: #007acc;
                    color: white;
                }
                QStatusBar {
                    background-color: #007acc;
                    color: white;
                }
                QCheckBox {
                    color: #333333;
                    spacing: 8px;
                }
                QRadioButton {
                    color: #333333;
                    spacing: 8px;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #ced4da;
                }
                QSlider::groove:horizontal {
                    height: 6px;
                    background: #dee2e6;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    width: 16px;
                    height: 16px;
                    margin: -5px 0;
                    background: #007acc;
                    border-radius: 8px;
                }
            """

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_paths = [url.toLocalFile() for url in urls]
            self.load_files(file_paths)

    def restore_geometry(self):
        """恢复窗口位置和大小"""
        geometry = self.config.get_window_geometry()
        if geometry:
            self.move(geometry.get("x", 100), geometry.get("y", 100))
            self.resize(geometry.get("width", 1200), geometry.get("height", 800))

    def closeEvent(self, event):
        """关闭事件"""
        geometry = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height()
        }
        self.config.save_window_geometry(geometry)
        self.config.save()
        event.accept()
