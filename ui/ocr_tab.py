"""
OCR识别标签页
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QLineEdit, QFileDialog, QProgressBar, QTextEdit,
    QSplitter, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.ocr_engine import OCREngine, OCROptions, OCRLanguage
from core.converter import PDFConverter
from utils.config import ConfigManager
from utils.file_utils import is_pdf_file, is_image_file


class OCRThread(QThread):
    """OCR识别线程"""
    finished = pyqtSignal(dict)

    def __init__(self, engine, file_path, page_num, options):
        super().__init__()
        self.engine = engine
        self.file_path = file_path
        self.page_num = page_num
        self.options = options

    def run(self):
        if is_pdf_file(self.file_path):
            result = self.engine.recognize_pdf_page(
                self.file_path, self.page_num, self.options
            )
        else:
            result = self.engine.recognize_file(self.file_path, self.options)

        self.finished.emit({
            "success": result.success,
            "text": result.text,
            "confidence": result.confidence,
            "error": result.error_message
        })


class OCRTab(QWidget):
    """OCR识别标签页"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.ocr_engine = OCREngine()
        self.pdf_converter = PDFConverter()
        self.current_file = None
        self.current_page = 0
        self.total_pages = 0
        self.ocr_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 左侧：文件和预览
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        file_btn_layout = QHBoxLayout()
        self.open_pdf_btn = QPushButton("打开PDF")
        self.open_pdf_btn.clicked.connect(self.open_pdf)
        self.open_image_btn = QPushButton("打开图片")
        self.open_image_btn.clicked.connect(self.open_image)
        file_btn_layout.addWidget(self.open_pdf_btn)
        file_btn_layout.addWidget(self.open_image_btn)
        file_layout.addLayout(file_btn_layout)

        self.file_label = QLabel("未选择文件")
        file_layout.addWidget(self.file_label)

        left_layout.addWidget(file_group)

        # 预览区域
        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("选择文件以预览")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        preview_layout.addWidget(self.preview_label)

        # 页面导航（PDF）
        self.page_nav_widget = QWidget()
        page_nav_layout = QHBoxLayout(self.page_nav_widget)
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("第 0/0 页")
        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.next_page)

        page_nav_layout.addWidget(self.prev_btn)
        page_nav_layout.addWidget(self.page_label, 1, Qt.AlignmentFlag.AlignCenter)
        page_nav_layout.addWidget(self.next_btn)
        preview_layout.addWidget(self.page_nav_widget)

        self.page_nav_widget.setVisible(False)
        left_layout.addWidget(preview_group)

        # 右侧：设置和结果
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # OCR设置
        settings_group = QGroupBox("OCR设置")
        settings_layout = QVBoxLayout(settings_group)

        # 语言选择
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("识别语言:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            "中文+英文", "简体中文", "繁体中文", "英文", "日文", "韩文"
        ])
        lang_row.addWidget(self.lang_combo)
        settings_layout.addLayout(lang_row)

        # DPI设置
        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("识别DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(150, 600)
        self.dpi_spin.setValue(self.config.get("ocr_dpi", 300))
        dpi_row.addWidget(self.dpi_spin)
        settings_layout.addLayout(dpi_row)

        # 预处理选项
        self.preprocess_check = QCheckBox("图片预处理（提高准确率）")
        self.preprocess_check.setChecked(True)
        settings_layout.addWidget(self.preprocess_check)

        self.grayscale_check = QCheckBox("灰度化")
        self.grayscale_check.setChecked(True)
        settings_layout.addWidget(self.grayscale_check)

        self.threshold_check = QCheckBox("二值化")
        self.threshold_check.setChecked(True)
        settings_layout.addWidget(self.threshold_check)

        right_layout.addWidget(settings_group)

        # 识别按钮
        self.recognize_btn = QPushButton("开始识别")
        self.recognize_btn.setMinimumHeight(40)
        self.recognize_btn.clicked.connect(self.start_recognize)
        right_layout.addWidget(self.recognize_btn)

        # 状态
        self.status_label = QLabel("")
        right_layout.addWidget(self.status_label)

        # 识别结果
        result_group = QGroupBox("识别结果")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setPlaceholderText("识别结果将显示在这里...")
        result_layout.addWidget(self.result_text)

        # 导出按钮
        export_layout = QHBoxLayout()
        self.export_txt_btn = QPushButton("导出TXT")
        self.export_txt_btn.clicked.connect(self.export_txt)
        self.export_docx_btn = QPushButton("导出Word")
        self.export_docx_btn.clicked.connect(self.export_docx)
        self.copy_btn = QPushButton("复制文本")
        self.copy_btn.clicked.connect(self.copy_text)

        export_layout.addWidget(self.export_txt_btn)
        export_layout.addWidget(self.export_docx_btn)
        export_layout.addWidget(self.copy_btn)
        result_layout.addLayout(export_layout)

        right_layout.addWidget(result_group)

        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

        # 检查OCR是否可用
        if not self.ocr_engine.is_available:
            self.recognize_btn.setEnabled(False)
            self.status_label.setText("⚠️ Tesseract未安装，OCR功能不可用")

    def open_pdf(self):
        """打开PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if file_path:
            self.load_file(file_path)

    def open_image(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff);;所有文件 (*.*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """加载文件"""
        self.current_file = file_path
        self.file_label.setText(os.path.basename(file_path))

        if is_pdf_file(file_path):
            info = self.pdf_converter.get_pdf_info(file_path)
            self.total_pages = info.get("pages", 0)
            self.current_page = 0
            self.page_nav_widget.setVisible(True)
            self.update_page_label()
            self.show_preview()
        else:
            self.total_pages = 1
            self.current_page = 0
            self.page_nav_widget.setVisible(False)
            self.show_preview()

    def show_preview(self):
        """显示预览"""
        if not self.current_file:
            return

        if is_pdf_file(self.current_file):
            img = self.pdf_converter.render_page_preview(
                self.current_file, self.current_page, 400, 500
            )
        else:
            from PIL import Image
            img = Image.open(self.current_file)
            # 缩放
            ratio = min(400 / img.width, 500 / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        if img:
            from PyQt6.QtGui import QImage, QPixmap
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

    def get_ocr_options(self) -> OCROptions:
        """获取OCR选项"""
        lang_map = {
            "中文+英文": OCRLanguage.CHINESE_ENG,
            "简体中文": OCRLanguage.CHINESE_SIMPLIFIED,
            "繁体中文": OCRLanguage.CHINESE_TRADITIONAL,
            "英文": OCRLanguage.ENGLISH,
            "日文": OCRLanguage.JAPANESE,
            "韩文": OCRLanguage.KOREAN
        }

        return OCROptions(
            language=lang_map.get(self.lang_combo.currentText(), OCRLanguage.CHINESE_ENG),
            preprocess=self.preprocess_check.isChecked(),
            grayscale=self.grayscale_check.isChecked(),
            threshold=self.threshold_check.isChecked(),
            dpi=self.dpi_spin.value()
        )

    def start_recognize(self):
        """开始识别"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先选择文件！")
            return

        if not self.ocr_engine.is_available:
            QMessageBox.warning(
                self,
                "OCR不可用",
                "Tesseract未安装！\n\n"
                "请安装Tesseract OCR：\n"
                "1. 下载: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "2. 安装时选择中文语言包\n"
                "3. 将安装目录添加到系统PATH"
            )
            return

        options = self.get_ocr_options()

        self.recognize_btn.setEnabled(False)
        self.status_label.setText("正在识别...")

        self.ocr_thread = OCRThread(
            self.ocr_engine,
            self.current_file,
            self.current_page,
            options
        )
        self.ocr_thread.finished.connect(self.on_recognize_complete)
        self.ocr_thread.start()

    def on_recognize_complete(self, result: dict):
        """识别完成"""
        self.recognize_btn.setEnabled(True)

        if result["success"]:
            self.result_text.setText(result["text"])
            self.status_label.setText(
                f"识别完成 - 置信度: {result['confidence']:.1f}%"
            )
        else:
            self.status_label.setText(f"识别失败: {result['error']}")
            QMessageBox.warning(self, "识别失败", result["error"])

    def export_txt(self):
        """导出为TXT"""
        text = self.result_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "没有识别结果可导出！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存TXT文件",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )

        if file_path:
            from core.ocr_engine import OCREngine
            if OCREngine.save_as_text(text, file_path):
                QMessageBox.information(self, "导出成功", f"文件已保存到: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "保存文件失败！")

    def export_docx(self):
        """导出为Word"""
        text = self.result_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "没有识别结果可导出！")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存Word文件",
            "",
            "Word文件 (*.docx);;所有文件 (*.*)"
        )

        if file_path:
            from core.ocr_engine import OCREngine
            if OCREngine.save_as_docx(text, file_path):
                QMessageBox.information(self, "导出成功", f"文件已保存到: {file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "保存文件失败！")

    def copy_text(self):
        """复制文本"""
        text = self.result_text.toPlainText()
        if text:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self.status_label.setText("已复制到剪贴板")
