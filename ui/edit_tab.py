"""
编辑功能标签页
包含水印、裁剪、合并功能
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox,
    QLineEdit, QFileDialog, QProgressBar, QListWidget,
    QListWidgetItem, QTabWidget, QSlider, QMessageBox,
    QColorDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from core.watermark import (
    WatermarkProcessor, TextWatermarkOptions,
    ImageWatermarkOptions, WatermarkPosition
)
from core.cropper import ImageCropper, CropOptions, CropMode
from core.merger import ImageMerger, MergeOptions, MergeMode
from utils.config import ConfigManager
from utils.file_utils import is_image_file, get_output_path


class EditTab(QWidget):
    """编辑功能标签页"""

    def __init__(self, config: ConfigManager):
        super().__init__()
        self.config = config
        self.current_files = []
        self.watermark_color = (128, 128, 128)

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 文件列表
        file_group = QGroupBox("文件列表")
        file_layout = QVBoxLayout(file_group)

        self.file_list = QListWidget()
        file_layout.addWidget(self.file_list)

        file_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加图片")
        self.add_btn.clicked.connect(self.add_files)
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("清空列表")
        self.clear_btn.clicked.connect(self.clear_files)

        file_btn_layout.addWidget(self.add_btn)
        file_btn_layout.addWidget(self.remove_btn)
        file_btn_layout.addWidget(self.clear_btn)
        file_layout.addLayout(file_btn_layout)

        layout.addWidget(file_group)

        # 功能标签页
        self.func_tabs = QTabWidget()

        # 水印标签页
        self.watermark_tab = self.create_watermark_tab()
        self.func_tabs.addTab(self.watermark_tab, "水印")

        # 裁剪标签页
        self.crop_tab = self.create_crop_tab()
        self.func_tabs.addTab(self.crop_tab, "裁剪")

        # 合并标签页
        self.merge_tab = self.create_merge_tab()
        self.func_tabs.addTab(self.merge_tab, "合并")

        layout.addWidget(self.func_tabs)

        # 输出设置和执行
        bottom_layout = QHBoxLayout()

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出目录...")
        self.output_dir_btn = QPushButton("浏览")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_dir_btn)

        bottom_layout.addLayout(output_layout)

        self.execute_btn = QPushButton("执行")
        self.execute_btn.setMinimumHeight(35)
        self.execute_btn.clicked.connect(self.execute)
        bottom_layout.addWidget(self.execute_btn)

        layout.addLayout(bottom_layout)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def create_watermark_tab(self) -> QWidget:
        """创建水印设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 水印类型
        type_group = QGroupBox("水印类型")
        type_layout = QVBoxLayout(type_group)

        self.wm_text_radio = QRadioButton("文字水印")
        self.wm_text_radio.setChecked(True)
        self.wm_image_radio = QRadioButton("图片水印")

        wm_type_group = QButtonGroup(self)
        wm_type_group.addButton(self.wm_text_radio)
        wm_type_group.addButton(self.wm_image_radio)

        type_layout.addWidget(self.wm_text_radio)
        type_layout.addWidget(self.wm_image_radio)
        layout.addWidget(type_group)

        # 文字水印设置
        self.wm_text_group = QGroupBox("文字水印设置")
        wm_text_layout = QVBoxLayout(self.wm_text_group)

        # 水印文字
        text_row = QHBoxLayout()
        text_row.addWidget(QLabel("水印文字:"))
        self.wm_text_edit = QLineEdit("水印")
        text_row.addWidget(self.wm_text_edit)
        wm_text_layout.addLayout(text_row)

        # 字体大小
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("字体大小:"))
        self.wm_size_spin = QSpinBox()
        self.wm_size_spin.setRange(12, 200)
        self.wm_size_spin.setValue(36)
        size_row.addWidget(self.wm_size_spin)
        wm_text_layout.addLayout(size_row)

        # 透明度
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("透明度:"))
        self.wm_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.wm_opacity_slider.setRange(0, 255)
        self.wm_opacity_slider.setValue(128)
        self.wm_opacity_label = QLabel("50%")
        self.wm_opacity_slider.valueChanged.connect(
            lambda v: self.wm_opacity_label.setText(f"{int(v/255*100)}%")
        )
        opacity_row.addWidget(self.wm_opacity_slider)
        opacity_row.addWidget(self.wm_opacity_label)
        wm_text_layout.addLayout(opacity_row)

        # 旋转角度
        rotation_row = QHBoxLayout()
        rotation_row.addWidget(QLabel("旋转角度:"))
        self.wm_rotation_spin = QSpinBox()
        self.wm_rotation_spin.setRange(-180, 180)
        self.wm_rotation_spin.setValue(30)
        rotation_row.addWidget(self.wm_rotation_spin)
        wm_text_layout.addLayout(rotation_row)

        # 字体颜色
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("字体颜色:"))
        self.wm_color_btn = QPushButton()
        self.wm_color_btn.setFixedSize(50, 30)
        self.update_color_button()
        self.wm_color_btn.clicked.connect(self.select_color)
        color_row.addWidget(self.wm_color_btn)
        color_row.addStretch()
        wm_text_layout.addLayout(color_row)

        layout.addWidget(self.wm_text_group)

        # 图片水印设置
        self.wm_image_group = QGroupBox("图片水印设置")
        wm_image_layout = QVBoxLayout(self.wm_image_group)

        image_row = QHBoxLayout()
        image_row.addWidget(QLabel("水印图片:"))
        self.wm_image_edit = QLineEdit()
        self.wm_image_edit.setPlaceholderText("选择水印图片...")
        self.wm_image_btn = QPushButton("浏览")
        self.wm_image_btn.clicked.connect(self.select_watermark_image)
        image_row.addWidget(self.wm_image_edit)
        image_row.addWidget(self.wm_image_btn)
        wm_image_layout.addLayout(image_row)

        # 缩放比例
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("缩放比例:"))
        self.wm_scale_spin = QSpinBox()
        self.wm_scale_spin.setRange(5, 100)
        self.wm_scale_spin.setValue(20)
        self.wm_scale_spin.setSuffix("%")
        scale_row.addWidget(self.wm_scale_spin)
        wm_image_layout.addLayout(scale_row)

        self.wm_image_group.setVisible(False)
        layout.addWidget(self.wm_image_group)

        # 切换水印类型
        self.wm_text_radio.toggled.connect(self.toggle_watermark_type)

        # 水印位置
        pos_group = QGroupBox("水印位置")
        pos_layout = QVBoxLayout(pos_group)

        self.wm_position_combo = QComboBox()
        self.wm_position_combo.addItems([
            "居中", "左上角", "顶部居中", "右上角",
            "左下角", "底部居中", "右下角", "平铺"
        ])
        pos_layout.addWidget(self.wm_position_combo)

        layout.addWidget(pos_group)

        layout.addStretch()
        return widget

    def create_crop_tab(self) -> QWidget:
        """创建裁剪设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 裁剪模式
        mode_group = QGroupBox("裁剪模式")
        mode_layout = QVBoxLayout(mode_group)

        self.crop_ratio_radio = QRadioButton("按比例裁剪")
        self.crop_ratio_radio.setChecked(True)
        self.crop_center_radio = QRadioButton("居中裁剪")
        self.crop_percent_radio = QRadioButton("按百分比裁剪")

        crop_mode_group = QButtonGroup(self)
        crop_mode_group.addButton(self.crop_ratio_radio)
        crop_mode_group.addButton(self.crop_center_radio)
        crop_mode_group.addButton(self.crop_percent_radio)

        mode_layout.addWidget(self.crop_ratio_radio)
        mode_layout.addWidget(self.crop_center_radio)
        mode_layout.addWidget(self.crop_percent_radio)
        layout.addWidget(mode_group)

        # 比例设置
        self.ratio_group = QGroupBox("比例设置")
        ratio_layout = QHBoxLayout(self.ratio_group)

        self.ratio_w_spin = QSpinBox()
        self.ratio_w_spin.setRange(1, 32)
        self.ratio_w_spin.setValue(16)
        ratio_layout.addWidget(self.ratio_w_spin)
        ratio_layout.addWidget(QLabel(":"))
        self.ratio_h_spin = QSpinBox()
        self.ratio_h_spin.setRange(1, 32)
        self.ratio_h_spin.setValue(9)
        ratio_layout.addWidget(self.ratio_h_spin)

        # 常用比例
        ratio_layout.addWidget(QLabel("常用:"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["自定义", "16:9", "4:3", "1:1", "3:2", "2:3"])
        self.ratio_combo.currentTextChanged.connect(self.on_ratio_preset)
        ratio_layout.addWidget(self.ratio_combo)

        layout.addWidget(self.ratio_group)

        # 居中裁剪设置
        self.center_group = QGroupBox("裁剪尺寸")
        center_layout = QHBoxLayout(self.center_group)

        center_layout.addWidget(QLabel("宽度:"))
        self.crop_w_spin = QSpinBox()
        self.crop_w_spin.setRange(10, 10000)
        self.crop_w_spin.setValue(800)
        center_layout.addWidget(self.crop_w_spin)

        center_layout.addWidget(QLabel("高度:"))
        self.crop_h_spin = QSpinBox()
        self.crop_h_spin.setRange(10, 10000)
        self.crop_h_spin.setValue(600)
        center_layout.addWidget(self.crop_h_spin)

        self.center_group.setVisible(False)
        layout.addWidget(self.center_group)

        # 百分比设置
        self.percent_group = QGroupBox("百分比设置")
        percent_layout = QVBoxLayout(self.percent_group)

        for label, attr in [("上边距:", "crop_top"), ("下边距:", "crop_bottom"),
                            ("左边距:", "crop_left"), ("右边距:", "crop_right")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            spin = QSpinBox()
            spin.setRange(0, 50)
            spin.setValue(10)
            spin.setSuffix("%")
            setattr(self, attr, spin)
            row.addWidget(spin)
            percent_layout.addLayout(row)

        self.percent_group.setVisible(False)
        layout.addWidget(self.percent_group)

        # 切换裁剪模式
        self.crop_ratio_radio.toggled.connect(self.toggle_crop_mode)
        self.crop_center_radio.toggled.connect(self.toggle_crop_mode)
        self.crop_percent_radio.toggled.connect(self.toggle_crop_mode)

        layout.addStretch()
        return widget

    def create_merge_tab(self) -> QWidget:
        """创建合并设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 合并模式
        mode_group = QGroupBox("合并模式")
        mode_layout = QVBoxLayout(mode_group)

        self.merge_pdf_radio = QRadioButton("合并为PDF")
        self.merge_pdf_radio.setChecked(True)
        self.merge_h_radio = QRadioButton("水平拼接")
        self.merge_v_radio = QRadioButton("垂直拼接")
        self.merge_grid_radio = QRadioButton("网格拼接")

        merge_mode_group = QButtonGroup(self)
        merge_mode_group.addButton(self.merge_pdf_radio)
        merge_mode_group.addButton(self.merge_h_radio)
        merge_mode_group.addButton(self.merge_v_radio)
        merge_mode_group.addButton(self.merge_grid_radio)

        mode_layout.addWidget(self.merge_pdf_radio)
        mode_layout.addWidget(self.merge_h_radio)
        mode_layout.addWidget(self.merge_v_radio)
        mode_layout.addWidget(self.merge_grid_radio)
        layout.addWidget(mode_group)

        # 网格设置
        self.grid_group = QGroupBox("网格设置")
        grid_layout = QHBoxLayout(self.grid_group)

        grid_layout.addWidget(QLabel("列数:"))
        self.grid_cols_spin = QSpinBox()
        self.grid_cols_spin.setRange(1, 10)
        self.grid_cols_spin.setValue(2)
        grid_layout.addWidget(self.grid_cols_spin)

        self.grid_group.setVisible(False)
        layout.addWidget(self.grid_group)

        # 间距设置
        gap_group = QGroupBox("间距设置")
        gap_layout = QHBoxLayout(gap_group)

        gap_layout.addWidget(QLabel("间距:"))
        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 100)
        self.gap_spin.setValue(10)
        self.gap_spin.setSuffix("px")
        gap_layout.addWidget(self.gap_spin)

        layout.addWidget(gap_group)

        # 切换合并模式
        self.merge_grid_radio.toggled.connect(lambda checked: self.grid_group.setVisible(checked))

        layout.addStretch()
        return widget

    def add_files(self):
        """添加文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif *.webp);;所有文件 (*.*)"
        )
        if file_paths:
            for path in file_paths:
                if is_image_file(path):
                    item = QListWidgetItem(os.path.basename(path))
                    item.setData(Qt.ItemDataRole.UserRole, path)
                    self.file_list.addItem(item)

    def remove_selected(self):
        """移除选中文件"""
        current = self.file_list.currentRow()
        if current >= 0:
            self.file_list.takeItem(current)

    def clear_files(self):
        """清空文件列表"""
        self.file_list.clear()

    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_dir_edit.text()
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def toggle_watermark_type(self, checked):
        """切换水印类型"""
        self.wm_text_group.setVisible(checked)
        self.wm_image_group.setVisible(not checked)

    def select_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(QColor(*self.watermark_color), self)
        if color.isValid():
            self.watermark_color = (color.red(), color.green(), color.blue())
            self.update_color_button()

    def update_color_button(self):
        """更新颜色按钮样式"""
        color = QColor(*self.watermark_color)
        self.wm_color_btn.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #999;"
        )

    def select_watermark_image(self):
        """选择水印图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择水印图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if file_path:
            self.wm_image_edit.setText(file_path)

    def toggle_crop_mode(self):
        """切换裁剪模式"""
        self.ratio_group.setVisible(self.crop_ratio_radio.isChecked())
        self.center_group.setVisible(self.crop_center_radio.isChecked())
        self.percent_group.setVisible(self.crop_percent_radio.isChecked())

    def on_ratio_preset(self, text):
        """选择预设比例"""
        presets = {
            "16:9": (16, 9),
            "4:3": (4, 3),
            "1:1": (1, 1),
            "3:2": (3, 2),
            "2:3": (2, 3)
        }
        if text in presets:
            w, h = presets[text]
            self.ratio_w_spin.setValue(w)
            self.ratio_h_spin.setValue(h)

    def get_position_enum(self) -> WatermarkPosition:
        """获取水印位置枚举"""
        position_map = {
            "居中": WatermarkPosition.CENTER,
            "左上角": WatermarkPosition.TOP_LEFT,
            "顶部居中": WatermarkPosition.TOP_CENTER,
            "右上角": WatermarkPosition.TOP_RIGHT,
            "左下角": WatermarkPosition.BOTTOM_LEFT,
            "底部居中": WatermarkPosition.BOTTOM_CENTER,
            "右下角": WatermarkPosition.BOTTOM_RIGHT,
            "平铺": WatermarkPosition.TILE
        }
        return position_map.get(self.wm_position_combo.currentText(), WatermarkPosition.CENTER)

    def get_files(self) -> list:
        """获取文件列表"""
        files = []
        for i in range(self.file_list.count()):
            files.append(self.file_list.item(i).data(Qt.ItemDataRole.UserRole))
        return files

    def execute(self):
        """执行编辑操作"""
        files = self.get_files()
        if not files:
            QMessageBox.warning(self, "警告", "请先添加图片文件！")
            return

        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录！")
            return

        # 根据当前标签页执行不同操作
        current_tab = self.func_tabs.currentIndex()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(files))

        success_count = 0
        fail_count = 0

        for i, file_path in enumerate(files):
            try:
                output_path = get_output_path(file_path, output_dir, "edited")

                if current_tab == 0:  # 水印
                    success = self.execute_watermark(file_path, output_path)
                elif current_tab == 1:  # 裁剪
                    success = self.execute_crop(file_path, output_path)
                elif current_tab == 2:  # 合并
                    # 合并功能单独处理
                    success = True
                else:
                    success = False

                if success:
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                fail_count += 1
                print(f"处理失败: {e}")

            self.progress_bar.setValue(i + 1)

        self.progress_bar.setVisible(False)

        if current_tab == 2:  # 合并
            self.execute_merge(files, output_dir)
        else:
            self.status_label.setText(f"处理完成: {success_count} 成功, {fail_count} 失败")
            QMessageBox.information(
                self,
                "处理完成",
                f"成功: {success_count}\n失败: {fail_count}"
            )

    def execute_watermark(self, input_path: str, output_path: str) -> bool:
        """执行水印操作"""
        position = self.get_position_enum()

        if self.wm_text_radio.isChecked():
            options = TextWatermarkOptions(
                text=self.wm_text_edit.text(),
                font_size=self.wm_size_spin.value(),
                font_color=self.watermark_color,
                opacity=self.wm_opacity_slider.value(),
                position=position,
                rotation=self.wm_rotation_spin.value()
            )
            return WatermarkProcessor.add_watermark_to_file(
                input_path, output_path, options, is_image_watermark=False
            )
        else:
            wm_path = self.wm_image_edit.text()
            if not wm_path:
                QMessageBox.warning(self, "警告", "请选择水印图片！")
                return False

            options = ImageWatermarkOptions(
                watermark_path=wm_path,
                opacity=128,
                position=position,
                scale=self.wm_scale_spin.value() / 100.0
            )
            return WatermarkProcessor.add_watermark_to_file(
                input_path, output_path, options, is_image_watermark=True
            )

    def execute_crop(self, input_path: str, output_path: str) -> bool:
        """执行裁剪操作"""
        if self.crop_ratio_radio.isChecked():
            options = CropOptions(
                mode=CropMode.RATIO,
                ratio=(self.ratio_w_spin.value(), self.ratio_h_spin.value())
            )
        elif self.crop_center_radio.isChecked():
            options = CropOptions(
                mode=CropMode.CENTER,
                center_size=(self.crop_w_spin.value(), self.crop_h_spin.value())
            )
        else:
            options = CropOptions(
                mode=CropMode.PERCENTAGE,
                percentage=(
                    self.crop_left.value(),
                    self.crop_top.value(),
                    self.crop_right.value(),
                    self.crop_bottom.value()
                )
            )

        return ImageCropper.crop_file(input_path, output_path, options)

    def execute_merge(self, files: list, output_dir: str):
        """执行合并操作"""
        if self.merge_pdf_radio.isChecked():
            mode = MergeMode.TO_PDF
        elif self.merge_h_radio.isChecked():
            mode = MergeMode.HORIZONTAL
        elif self.merge_v_radio.isChecked():
            mode = MergeMode.VERTICAL
        else:
            mode = MergeMode.GRID

        options = MergeOptions(
            mode=mode,
            gap=self.gap_spin.value(),
            columns=self.grid_cols_spin.value()
        )

        if mode == MergeMode.TO_PDF:
            output_path = os.path.join(output_dir, "merged.pdf")
        else:
            output_path = os.path.join(output_dir, "merged.png")

        success = ImageMerger.merge_files(files, output_path, options)

        if success:
            self.status_label.setText(f"合并完成: {output_path}")
            QMessageBox.information(self, "合并完成", f"文件已保存到: {output_path}")
        else:
            self.status_label.setText("合并失败")
            QMessageBox.warning(self, "合并失败", "合并操作失败，请检查文件！")
