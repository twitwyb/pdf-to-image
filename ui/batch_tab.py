"""
批量处理标签页
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.converter import ConvertOptions, OutputFormat
from core.batch_processor import BatchProcessor, BatchTask, BatchProgress
from utils.config import ConfigManager
from utils.file_utils import get_pdf_files, get_file_size_str


class BatchThread(QThread):
    """批量处理线程"""
    progress = pyqtSignal(dict)
    file_complete = pyqtSignal(dict)
    all_complete = pyqtSignal()

    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        def progress_callback(progress: BatchProgress):
            self.progress.emit({
                "total_files": progress.total_files,
                "completed_files": progress.completed_files,
                "current_file": progress.current_file,
                "current_page": progress.current_page,
                "total_pages": progress.total_pages,
                "overall_progress": progress.overall_progress
            })

        def file_complete_callback(task: BatchTask):
            self.file_complete.emit({
                "path": task.pdf_path,
                "status": task.status,
                "results": task.results
            })

        self.processor.set_progress_callback(progress_callback)
        self.processor.set_file_complete_callback(file_complete_callback)
        self.processor.start()
        self.all_complete.emit()


class BatchTab(QWidget):
    """批量处理标签页"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.processor = BatchProcessor(max_workers=config.get("max_workers", 4))
        self.batch_thread = None

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 左侧：文件列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # 文件列表
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)

        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["文件名", "大小", "页数", "状态"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        file_layout.addWidget(self.file_table)

        # 文件操作按钮
        file_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加文件")
        self.add_btn.clicked.connect(self.add_files)
        self.add_dir_btn = QPushButton("添加文件夹")
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self.clear_files)

        file_btn_layout.addWidget(self.add_btn)
        file_btn_layout.addWidget(self.add_dir_btn)
        file_btn_layout.addWidget(self.remove_btn)
        file_btn_layout.addWidget(self.clear_btn)
        file_layout.addLayout(file_btn_layout)

        # 统计信息
        self.stats_label = QLabel("共 0 个文件")
        file_layout.addWidget(self.stats_label)

        left_layout.addWidget(file_group)

        # 右侧：设置和控制
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # 输出设置
        settings_group = QGroupBox("输出设置")
        settings_layout = QVBoxLayout(settings_group)

        # 格式选择
        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "BMP", "TIFF"])
        format_row.addWidget(self.format_combo)
        settings_layout.addLayout(format_row)

        # DPI设置
        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("DPI分辨率:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(self.config.get("default_dpi", 300))
        dpi_row.addWidget(self.dpi_spin)
        settings_layout.addLayout(dpi_row)

        # 质量设置
        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("图片质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(self.config.get("default_quality", 95))
        self.quality_spin.setSuffix("%")
        quality_row.addWidget(self.quality_spin)
        settings_layout.addLayout(quality_row)

        # 其他选项
        self.grayscale_check = QCheckBox("灰度模式")
        settings_layout.addWidget(self.grayscale_check)

        # 线程数设置
        workers_row = QHBoxLayout()
        workers_row.addWidget(QLabel("并发线程:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 8)
        self.workers_spin.setValue(self.config.get("max_workers", 4))
        workers_row.addWidget(self.workers_spin)
        settings_layout.addLayout(workers_row)

        right_layout.addWidget(settings_group)

        # 输出目录
        output_group = QGroupBox("输出目录")
        output_layout = QVBoxLayout(output_group)

        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        self.output_dir_btn = QPushButton("浏览")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(self.output_dir_btn)
        output_layout.addLayout(output_dir_layout)

        right_layout.addWidget(output_group)

        # 控制按钮
        control_group = QGroupBox("操作控制")
        control_layout = QVBoxLayout(control_group)

        self.start_btn = QPushButton("开始批量处理")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_batch)
        control_layout.addWidget(self.start_btn)

        # 控制按钮行
        btn_row = QHBoxLayout()
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_batch)

        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.cancel_btn)
        control_layout.addLayout(btn_row)

        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        control_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("就绪")
        control_layout.addWidget(self.progress_label)

        # 统计
        self.result_label = QLabel("")
        control_layout.addWidget(self.result_label)

        right_layout.addWidget(control_group)

        right_layout.addStretch()

        # 使用分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 300])

        layout.addWidget(splitter)

    def load_directory(self, dir_path: str):
        """加载目录中的PDF文件"""
        pdf_files = get_pdf_files(dir_path)
        self.add_files_to_list(pdf_files)

    def add_files(self):
        """添加文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择PDF文件",
            "",
            "PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        if file_paths:
            self.add_files_to_list(file_paths)

    def add_directory(self):
        """添加文件夹"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择文件夹",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.load_directory(dir_path)

    def add_files_to_list(self, file_paths: list):
        """添加文件到列表"""
        for path in file_paths:
            # 检查是否已存在
            existing = False
            for row in range(self.file_table.rowCount()):
                if self.file_table.item(row, 0).data(Qt.ItemDataRole.UserRole) == path:
                    existing = True
                    break

            if not existing and path.lower().endswith('.pdf'):
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)

                # 文件名
                name_item = QTableWidgetItem(os.path.basename(path))
                name_item.setData(Qt.ItemDataRole.UserRole, path)
                self.file_table.setItem(row, 0, name_item)

                # 文件大小
                try:
                    size = os.path.getsize(path)
                    size_item = QTableWidgetItem(get_file_size_str(size))
                except:
                    size_item = QTableWidgetItem("未知")
                self.file_table.setItem(row, 1, size_item)

                # 页数（延迟加载）
                pages_item = QTableWidgetItem("...")
                self.file_table.setItem(row, 2, pages_item)

                # 状态
                status_item = QTableWidgetItem("待处理")
                self.file_table.setItem(row, 3, status_item)

        self.update_stats()

    def remove_selected(self):
        """移除选中文件"""
        rows = set()
        for item in self.file_table.selectedItems():
            rows.add(item.row())

        for row in sorted(rows, reverse=True):
            self.file_table.removeRow(row)

        self.update_stats()

    def clear_files(self):
        """清空文件列表"""
        self.file_table.setRowCount(0)
        self.update_stats()

    def update_stats(self):
        """更新统计信息"""
        count = self.file_table.rowCount()
        self.stats_label.setText(f"共 {count} 个文件")

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

        return ConvertOptions(
            dpi=self.dpi_spin.value(),
            format=format_map[self.format_combo.currentText()],
            quality=self.quality_spin.value(),
            grayscale=self.grayscale_check.isChecked()
        )

    def start_batch(self):
        """开始批量处理"""
        if self.file_table.rowCount() == 0:
            QMessageBox.warning(self, "警告", "请先添加PDF文件！")
            return

        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录！")
            return

        # 获取设置
        options = self.get_convert_options()
        self.processor = BatchProcessor(max_workers=self.workers_spin.value())

        # 添加任务
        for row in range(self.file_table.rowCount()):
            file_path = self.file_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self.processor.add_task(file_path, output_dir, options)

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        # 启动处理线程
        self.batch_thread = BatchThread(self.processor)
        self.batch_thread.progress.connect(self.update_progress)
        self.batch_thread.file_complete.connect(self.on_file_complete)
        self.batch_thread.all_complete.connect(self.on_all_complete)
        self.batch_thread.start()

    def toggle_pause(self):
        """切换暂停状态"""
        if self.processor.is_paused:
            self.processor.resume()
            self.pause_btn.setText("暂停")
            self.progress_label.setText("处理中...")
        else:
            self.processor.pause()
            self.pause_btn.setText("继续")
            self.progress_label.setText("已暂停")

    def cancel_batch(self):
        """取消批量处理"""
        reply = QMessageBox.question(
            self,
            "确认取消",
            "确定要取消批量处理吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.processor.cancel()
            self.progress_label.setText("正在取消...")

    def update_progress(self, progress: dict):
        """更新进度"""
        self.progress_bar.setValue(int(progress["overall_progress"]))
        self.progress_label.setText(
            f"正在处理: {progress['current_file']} "
            f"({progress['current_page']}/{progress['total_pages']})"
        )

    def on_file_complete(self, info: dict):
        """文件处理完成"""
        # 更新表格状态
        for row in range(self.file_table.rowCount()):
            if self.file_table.item(row, 0).data(Qt.ItemDataRole.UserRole) == info["path"]:
                status = "成功" if info["status"] == "completed" else "失败"
                self.file_table.item(row, 3).setText(status)
                break

    def on_all_complete(self):
        """全部处理完成"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.pause_btn.setText("暂停")

        # 统计结果
        summary = self.processor.progress_summary
        self.result_label.setText(
            f"完成: {summary['completed']} 成功, {summary['failed']} 失败"
        )
        self.progress_label.setText("处理完成")

        QMessageBox.information(
            self,
            "批量处理完成",
            f"处理完成！\n成功: {summary['completed']}\n失败: {summary['failed']}"
        )
