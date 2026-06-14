"""
图片合并功能模块
支持多图合并为PDF、图片拼接
"""
import os
from PIL import Image
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MergeMode(Enum):
    """合并模式"""
    TO_PDF = "to_pdf"          # 多图合并为PDF
    HORIZONTAL = "horizontal"  # 水平拼接
    VERTICAL = "vertical"      # 垂直拼接
    GRID = "grid"              # 网格拼接


@dataclass
class MergeOptions:
    """合并选项"""
    mode: MergeMode = MergeMode.TO_PDF

    # PDF选项
    page_size: Optional[Tuple[int, int]] = None  # 页面尺寸(像素)，None表示使用第一张图尺寸
    fit_to_page: bool = True  # 是否适应页面
    margin: int = 0  # 边距(像素)

    # 拼接选项
    gap: int = 0  # 图片间距(像素)
    background_color: Tuple[int, int, int] = (255, 255, 255)  # 背景颜色

    # 网格选项
    columns: int = 2  # 网格列数


class ImageMerger:
    """图片合并器"""

    @staticmethod
    def merge_to_pdf(
        images: List[Image.Image],
        options: MergeOptions
    ) -> Image.Image:
        """多图合并为PDF（返回第一张图，实际保存时会处理多页）"""
        if not images:
            raise ValueError("没有图片可合并")

        # 如果指定了页面尺寸，调整所有图片
        if options.page_size:
            page_w, page_h = options.page_size
            processed = []
            for img in images:
                if options.fit_to_page:
                    # 适应页面，保持比例
                    ratio = min(page_w / img.width, page_h / img.height)
                    new_w = int(img.width * ratio)
                    new_h = int(img.height * ratio)
                    img = img.resize((new_w, new_h), Image.LANCZOS)

                # 创建页面
                page = Image.new("RGB", (page_w, page_h), options.background_color)
                # 居中放置
                x = (page_w - img.width) // 2
                y = (page_h - img.height) // 2
                if img.mode == "RGBA":
                    page.paste(img, (x, y), img)
                else:
                    page.paste(img, (x, y))
                processed.append(page)
            return processed

        return images

    @staticmethod
    def merge_horizontal(
        images: List[Image.Image],
        options: MergeOptions
    ) -> Image.Image:
        """水平拼接"""
        if not images:
            raise ValueError("没有图片可合并")

        # 统一高度
        max_height = max(img.height for img in images)
        total_width = sum(img.width for img in images) + options.gap * (len(images) - 1)

        # 创建画布
        result = Image.new("RGB", (total_width, max_height), options.background_color)

        x_offset = 0
        for img in images:
            # 垂直居中
            y_offset = (max_height - img.height) // 2
            if img.mode == "RGBA":
                result.paste(img, (x_offset, y_offset), img)
            else:
                result.paste(img, (x_offset, y_offset))
            x_offset += img.width + options.gap

        return result

    @staticmethod
    def merge_vertical(
        images: List[Image.Image],
        options: MergeOptions
    ) -> Image.Image:
        """垂直拼接"""
        if not images:
            raise ValueError("没有图片可合并")

        # 统一宽度
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images) + options.gap * (len(images) - 1)

        # 创建画布
        result = Image.new("RGB", (max_width, total_height), options.background_color)

        y_offset = 0
        for img in images:
            # 水平居中
            x_offset = (max_width - img.width) // 2
            if img.mode == "RGBA":
                result.paste(img, (x_offset, y_offset), img)
            else:
                result.paste(img, (x_offset, y_offset))
            y_offset += img.height + options.gap

        return result

    @staticmethod
    def merge_grid(
        images: List[Image.Image],
        options: MergeOptions
    ) -> Image.Image:
        """网格拼接"""
        if not images:
            raise ValueError("没有图片可合并")

        columns = options.columns
        rows = (len(images) + columns - 1) // columns

        # 计算每个单元格的最大尺寸
        max_cell_width = max(img.width for img in images)
        max_cell_height = max(img.height for img in images)

        # 计算总尺寸
        total_width = max_cell_width * columns + options.gap * (columns + 1)
        total_height = max_cell_height * rows + options.gap * (rows + 1)

        # 创建画布
        result = Image.new("RGB", (total_width, total_height), options.background_color)

        for idx, img in enumerate(images):
            row = idx // columns
            col = idx % columns

            # 计算位置（居中在单元格内）
            x = options.gap + col * (max_cell_width + options.gap) + (max_cell_width - img.width) // 2
            y = options.gap + row * (max_cell_height + options.gap) + (max_cell_height - img.height) // 2

            if img.mode == "RGBA":
                result.paste(img, (x, y), img)
            else:
                result.paste(img, (x, y))

        return result

    @staticmethod
    def merge_images(
        images: List[Image.Image],
        options: MergeOptions
    ) -> List[Image.Image] | Image.Image:
        """根据选项合并图片"""
        if options.mode == MergeMode.TO_PDF:
            return ImageMerger.merge_to_pdf(images, options)
        elif options.mode == MergeMode.HORIZONTAL:
            return ImageMerger.merge_horizontal(images, options)
        elif options.mode == MergeMode.VERTICAL:
            return ImageMerger.merge_vertical(images, options)
        elif options.mode == MergeMode.GRID:
            return ImageMerger.merge_grid(images, options)
        else:
            raise ValueError(f"不支持的合并模式: {options.mode}")

    @staticmethod
    def save_as_pdf(
        images: List[Image.Image],
        output_path: str,
        options: MergeOptions
    ) -> bool:
        """将多张图片保存为PDF"""
        try:
            if not images:
                return False

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 转换为RGB模式
            rgb_images = []
            for img in images:
                if img.mode == "RGBA":
                    # 创建白色背景
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    rgb_images.append(bg)
                elif img.mode != "RGB":
                    rgb_images.append(img.convert("RGB"))
                else:
                    rgb_images.append(img)

            # 如果需要调整大小
            if options.page_size:
                page_w, page_h = options.page_size
                processed = []
                for img in rgb_images:
                    if options.fit_to_page:
                        ratio = min(page_w / img.width, page_h / img.height)
                        new_w = int(img.width * ratio)
                        new_h = int(img.height * ratio)
                        img = img.resize((new_w, new_h), Image.LANCZOS)

                    page = Image.new("RGB", (page_w, page_h), options.background_color)
                    x = (page_w - img.width) // 2
                    y = (page_h - img.height) // 2
                    page.paste(img, (x, y))
                    processed.append(page)
                rgb_images = processed

            # 保存为PDF
            if len(rgb_images) == 1:
                rgb_images[0].save(output_path, "PDF")
            else:
                rgb_images[0].save(
                    output_path, "PDF",
                    save_all=True,
                    append_images=rgb_images[1:]
                )

            return True

        except Exception as e:
            print(f"保存PDF失败: {e}")
            return False

    @staticmethod
    def merge_files(
        input_paths: List[str],
        output_path: str,
        options: MergeOptions
    ) -> bool:
        """合并图片文件"""
        try:
            images = []
            for path in input_paths:
                img = Image.open(path)
                images.append(img)

            if options.mode == MergeMode.TO_PDF:
                return ImageMerger.save_as_pdf(images, output_path, options)
            else:
                result = ImageMerger.merge_images(images, options)

                # 保存时转换为RGB（如果保存为JPG）
                if output_path.lower().endswith(('.jpg', '.jpeg')):
                    result = result.convert("RGB")

                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                result.save(output_path)
                return True

        except Exception as e:
            print(f"合并失败: {e}")
            return False
