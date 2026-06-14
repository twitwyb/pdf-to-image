"""
PDF转图片标签页 - 优化版
支持拖拽、自动设置输出目录、DPI预设
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QListWidget,
    QListWidgetItem, QSplitter, QFrame, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

from core.converter import PDFConverter, ConvertOptions, OutputFormat
from utils.config import ConfigManager
from utils.file_utils import get_file_size_str, is_pdf_file


class ConvertThread(QThread):
    """转换线程"""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)

    def __init__(self, converter, pdf_path, output_dir, options):
        super().__init__()
        self.converter = converter
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.options = options

    def run(self):
        def progress_callback(current, total):
            self.progress.emit(current, total)

        self.converter.set_progress_callback(progress_callback)
        results = self.converter.convert_pdf(
            self.pdf_path,
            self.output_dir,
            self.options
        )
        self.finished.emit(results)


class ConvertTab(QWidget):
    """PDF转图片标签页 - 支持拖拽和DPI预设"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.converter = PDFConverter()
        self.current_file = None
        self.convert_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 左侧：文件列表和预览
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 文件列表
        file_group = QGroupBox("📁 文件列表")
        file_layout = QVBoxLayout(file_group)

        self.file_list = QListWidget()
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        self.file_list.setMinimumHeight(100)
        file_layout.addWidget(self.file_list)

        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ 添加文件")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton("➖ 移除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("🗑️ 清空列表")
        self.clear_btn.clicked.connect(self.clear_files)

        file_btn_layout.addWidget(self.add_btn)
        file_btn_layout.addWidget(self.remove_btn)
        file_btn_layout.addWidget(self.clear_btn)
        file_layout.addLayout(file_btn_layout)

        # 文件统计
        self.file_count_label = QLabel("共 0 个文件")
        file_layout.addWidget(self.file_count_label)

        left_layout.addWidget(file_group)

        # 预览区域
        preview_group = QGroupBox("👁️ 页面预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("选择PDF文件以预览\n\n支持拖拽文件到此处")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
        """)
        preview_layout.addWidget(self.preview_label)

        # 页面导航
        page_nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("第 0/0 页")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.clicked.connect(self.next_page)

        page_nav_layout.addWidget(self.prev_btn)
        page_nav_layout.addWidget(self.page_label, 1)
        page_nav_layout.addWidget(self.next_btn)
        preview_layout.addLayout(page_nav_layout)

        left_layout.addWidget(preview_group)

        # 右侧：设置面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 输出格式设置
        format_group = QGroupBox("⚙️ 输出设置")
        format_layout = QVBoxLayout(format_group)

        # 格式选择
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP", "TIFF"])
        self.format_combo.setCurrentText(self.config.get("default_format", "PNG").upper())
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        format_row.addWidget(self.format_combo)
        format_layout.addLayout(format_row)

        # DPI预设
        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("DPI分辨率:"))
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["72 (屏幕)", "150 (标准)", "300 (高清)", "600 (超高清)", "自定义"])
        self.dpi_combo.setCurrentText("300 (高清)")
        self.dpi_combo.currentTextChanged.connect(self.on_dpi_preset_changed)
        dpi_row.addWidget(self.dpi_combo)
        format_layout.addLayout(dpi_row)

        # 自定义DPI
        custom_dpi_row = QHBoxLayout()
        custom_dpi_row.addWidget(QLabel("自定义DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSingleStep(50)
        self.dpi_spin.setVisible(False)
        custom_dpi_row.addWidget(self.dpi_spin)
        format_layout.addLayout(custom_dpi_row)

        # 质量设置（JPG）
        self.quality_widget = QWidget()
        quality_row = QHBoxLayout(self.quality_widget)
        quality_row.setContentsMargins(0, 0, 0, 0)
        quality_row.addWidget(QLabel("图片质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(self.config.get("default_quality", 95))
        self.quality_spin.setSuffix("%")
        quality_row.addWidget(self.quality_spin)
        format_layout.addWidget(self.quality_widget)
        self.quality_widget.setVisible(False)

        # 其他选项
        options_layout = QHBoxLayout()
        self.grayscale_check = QCheckBox("灰度模式")
        self.alpha_check = QCheckBox("透明通道")
        options_layout.addWidget(self.grayscale_check)
        options_layout.addWidget(self.alpha_check)
        format_layout.addLayout(options_layout)

        right_layout.addWidget(format_group)

        # 页面范围设置
        range_group = QGroupBox("📄 页面范围")
        range_layout = QVBoxLayout(range_group)

        self.range_all = QRadioButton("全部页面")
        self.range_all.setChecked(True)
        self.range_custom = QRadioButton("自定义范围")

        range_btn_group = QButtonGroup(self)
        range_btn_group.addButton(self.range_all)
        range_btn_group.addButton(self.range_custom)

        range_layout.addWidget(self.range_all)
        range_layout.addWidget(self.range_custom)

        self.range_edit = QLineEdit()
        self.range_edit.setPlaceholderText("例如: 1-5,8,10-12")
        self.range_edit.setEnabled(False)
        self.range_custom.toggled.connect(self.range_edit.setEnabled)
        range_layout.addWidget(self.range_edit)

        right_layout.addWidget(range_group)

        # 输出目录设置
        output_group = QGroupBox("📂 输出目录")
        output_layout = QVBoxLayout(output_group)

        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        self.output_dir_btn = QPushButton("浏览")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        output_layout.addLayout(output_dir_layout)

        # 自动打开输出目录
        self.auto_open_check = QCheckBox("转换完成后自动打开输出目录")
        self.auto_open_check.setChecked(True)
        output_layout.addWidget(self.auto_open_check)

        # 文件名模板
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("文件名模板:"))
        self.template_edit = QLineEdit("{name}_page{page:03d}")
        self.template_edit.setToolTip("支持变量:\n{name} - 文件名\n{page} - 页码")
        template_layout.addWidget(self.template_edit)
        output_layout.addLayout(template_layout)

        right_layout.addWidget(output_group)

        # 转换按钮和进度
        action_group = QGroupBox("🚀 操作")
        action_layout = QVBoxLayout(action_group)

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumHeight(45)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34d058;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.convert_btn.clicked.connect(self.start_convert)
        action_layout.addWidget(self.convert_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        action_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.addWidget(self.status_label)

        right_layout.addWidget(action_group)

        right_layout.addStretch()

        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 350])

        layout.addWidget(splitter)

        # 文件信息
        self.current_page = 0
        self.total_pages = 0

    def on_format_changed(self, format_text):
        """格式改变时更新UI"""
        self.quality_widget.setVisible(format_text == "JPG")
        self.alpha_check.setVisible(format_text == "PNG")

    def on_dpi_preset_changed(self, preset):
        """DPI预设改变"""
        dpi_map = {
            "72 (屏幕)": 72,
            "150 (标准)": 150,
            "300 (高清)": 300,
            "600 (超高清)": 600,
        }
        if preset in dpi_map:
            self.dpi_spin.setValue(dpi_map[preset])
            self.dpi_spin.setVisible(False)
        else:
            self.dpi_spin.setVisible(True)

    def load_files(self, file_paths: list):
        """加载文件列表"""
        for path in file_paths:
            if is_pdf_file(path):
                # 检查是否已存在
                existing = False
                for i in range(self.file_list.count()):
                    if self.file_list.item(i).data(Qt.ItemDataRole.UserRole) == path:
                        existing = True
                        break

                if not existing:
                    item = QListWidgetItem(os.path.basename(path))
                    item.setData(Qt.ItemDataRole.UserRole, path)
                    item.setToolTip(path)
                    self.file_list.addItem(item)

        # 更新文件计数
        self.file_count_label.setText(f"共 {self.file_list.count()} 个文件")

        # 选中第一个
        if self.file_list.count() > 0 and self.file_list.currentItem() is None:
            self.file_list.setCurrentRow(0)

    def add_files(self):
        """添加文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if file_paths:
            self.load_files(file_paths)

    def remove_selected(self):
        """移除选中文件"""
        current = self.file_list.currentRow()
        if current >= 0:
            self.file_list.takeItem(current)
            self.file_count_label.setText(f"共 {self.file_list.count()} 个文件")

    def clear_files(self):
        """清空文件列表"""
        self.file_list.clear()
        self.current_file = None
        self.preview_label.setText("选择PDF文件以预览\n\n支持拖拽文件到此处")
        self.page_label.setText("第 0/0 页")
        self.file_count_label.setText("共 0 个文件")

    def on_file_selected(self, current, previous):
        """文件选中事件"""
        if current:
            file_path = current.data(Qt.ItemDataRole.UserRole)
            self.current_file = file_path
            self.current_page = 0

            # 获取PDF信息
            info = self.converter.get_pdf_info(file_path)
            self.total_pages = info.get("pages", 0)

            # 自动设置输出目录为PDF所在目录
            if not self.output_dir_edit.text():
                self.output_dir_edit.setText(os.path.dirname(file_path))

            # 更新页面标签
            self.update_page_label()

            # 显示预览
            self.show_preview()

    def show_preview(self):
        """显示页面预览"""
        if not self.current_file or self.total_pages == 0:
            return

        img = self.converter.render_page_preview(
            self.current_file, self.current_page, 400, 500
        )

        if img:
            # 转换为QPixmap
            if img.mode != "RGB":
                img = img.convert("RGB")

            qimg = QImage(
                img.tobytes(), img.width, img.height,
                img.width * 3, QImage.Format.Format_RGB888
            )

            pixmap = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(
                pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def update_page_label(self):
        """更新页面标签"""
        self.page_label.setText(f"第 {self.current_page + 1}/{self.total_pages} 页")

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page_label()
            self.show_preview()

    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_page_label()
            self.show_preview()

    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def get_convert_options(self) -> ConvertOptions:
        """获取转换选项"""
        format_map = {
            "PNG": OutputFormat.PNG,
            "JPG": OutputFormat.JPG,
            "BMP": OutputFormat.BMP,
            "TIFF": OutputFormat.TIFF
        }

        page_range = None
        if self.range_custom.isChecked():
            page_range = self.range_edit.text().strip()

        return ConvertOptions(
            dpi=self.dpi_spin.value(),
            format=format_map[self.format_combo.currentText()],
            quality=self.quality_spin.value(),
            page_range=page_range,
            grayscale=self.grayscale_check.isChecked(),
            alpha=self.alpha_check.isChecked()
        )

    def start_convert(self):
        """开始转换"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件！")
            return

        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录！")
            return

        # 获取转换选项
        options = self.get_convert_options()

        # 禁用按钮
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("转换中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 创建转换线程
        self.convert_thread = ConvertThread(
            self.converter,
            self.current_file,
            output_dir,
            options
        )
        self.convert_thread.progress.connect(self.update_progress)
        self.convert_thread.finished.connect(self.convert_finished)
        self.convert_thread.start()

    def update_progress(self, current, total):
        """更新进度"""
        progress = int(current / total * 100)
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"{progress}% ({current}/{total})")
        self.status_label.setText(f"正在转换: {current}/{total} 页")

    def convert_finished(self, results):
        """转换完成"""
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("开始转换")
        self.progress_bar.setVisible(False)

        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        output_dir = self.output_dir_edit.text()

        if fail_count == 0:
            self.status_label.setText(f"✅ 转换完成: {success_count} 页成功")

            # 自动打开输出目录
            if self.auto_open_check.isChecked():
                os.startfile(output_dir)

            QMessageBox.information(
                self,
                "转换完成",
                f"✅ 成功转换 {success_count} 页图片！\n\n📁 输出目录: {output_dir}"
            )
        else:
            self.status_label.setText(f"⚠️ 转换完成: {success_count} 成功, {fail_count} 失败")
            errors = [r.error_message for r in results if r.error_message]
            QMessageBox.warning(
                self,
                "转换完成（有错误）",
                f"成功: {success_count} 页\n失败: {fail_count} 页\n\n错误信息:\n" + "\n".join(errors[:5])
            )
