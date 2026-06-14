"""
图片裁剪功能模块
"""
import os
from PIL import Image
from typing import Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CropMode(Enum):
    """裁剪模式"""
    CUSTOM = "custom"          # 自定义区域
    RATIO = "ratio"            # 按比例
    CENTER = "center"          # 居中裁剪
    PERCENTAGE = "percentage"  # 按百分比


@dataclass
class CropOptions:
    """裁剪选项"""
    mode: CropMode = CropMode.CUSTOM

    # 自定义区域模式 (left, top, right, bottom)
    box: Optional[Tuple[int, int, int, int]] = None

    # 比例模式
    ratio: Optional[Tuple[int, int]] = None  # 如 (16, 9), (4, 3)

    # 居中裁剪尺寸
    center_size: Optional[Tuple[int, int]] = None  # (width, height)

    # 百分比模式
    percentage: Optional[Tuple[float, float, float, float]] = None  # (left%, top%, right%, bottom%)


class ImageCropper:
    """图片裁剪器"""

    @staticmethod
    def crop_custom(image: Image.Image, box: Tuple[int, int, int, int]) -> Image.Image:
        """自定义区域裁剪"""
        left, top, right, bottom = box

        # 边界检查
        left = max(0, min(left, image.width))
        top = max(0, min(top, image.height))
        right = max(left, min(right, image.width))
        bottom = max(top, min(bottom, image.height))

        return image.crop((left, top, right, bottom))

    @staticmethod
    def crop_by_ratio(image: Image.Image, ratio: Tuple[int, int]) -> Image.Image:
        """按比例裁剪（从中心裁剪到最大匹配区域）"""
        target_ratio = ratio[0] / ratio[1]
        img_ratio = image.width / image.height

        if img_ratio > target_ratio:
            # 图片更宽，裁剪宽度
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2
            return image.crop((left, 0, left + new_width, image.height))
        else:
            # 图片更高，裁剪高度
            new_height = int(image.width / target_ratio)
            top = (image.height - new_height) // 2
            return image.crop((0, top, image.width, top + new_height))

    @staticmethod
    def crop_center(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        """居中裁剪到指定尺寸"""
        target_w, target_h = size
        target_w = min(target_w, image.width)
        target_h = min(target_h, image.height)

        left = (image.width - target_w) // 2
        top = (image.height - target_h) // 2

        return image.crop((left, top, left + target_w, top + target_h))

    @staticmethod
    def crop_percentage(
        image: Image.Image,
        percentage: Tuple[float, float, float, float]
    ) -> Image.Image:
        """按百分比裁剪"""
        left_pct, top_pct, right_pct, bottom_pct = percentage

        left = int(image.width * left_pct / 100)
        top = int(image.height * top_pct / 100)
        right = int(image.width * (100 - right_pct) / 100)
        bottom = int(image.height * (100 - bottom_pct) / 100)

        return image.crop((left, top, right, bottom))

    @staticmethod
    def crop_image(image: Image.Image, options: CropOptions) -> Image.Image:
        """根据选项裁剪图片"""
        if options.mode == CropMode.CUSTOM:
            if options.box is None:
                raise ValueError("自定义模式需要提供box参数")
            return ImageCropper.crop_custom(image, options.box)

        elif options.mode == CropMode.RATIO:
            if options.ratio is None:
                raise ValueError("比例模式需要提供ratio参数")
            return ImageCropper.crop_by_ratio(image, options.ratio)

        elif options.mode == CropMode.CENTER:
            if options.center_size is None:
                raise ValueError("居中模式需要提供center_size参数")
            return ImageCropper.crop_center(image, options.center_size)

        elif options.mode == CropMode.PERCENTAGE:
            if options.percentage is None:
                raise ValueError("百分比模式需要提供percentage参数")
            return ImageCropper.crop_percentage(image, options.percentage)

        else:
            raise ValueError(f"不支持的裁剪模式: {options.mode}")

    @staticmethod
    def crop_file(
        input_path: str,
        output_path: str,
        options: CropOptions
    ) -> bool:
        """裁剪图片文件"""
        try:
            image = Image.open(input_path)
            result = ImageCropper.crop_image(image, options)

            # 保存时转换为RGB（如果保存为JPG）
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                result = result.convert("RGB")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result.save(output_path)
            return True

        except Exception as e:
            print(f"裁剪失败: {e}")
            return False

    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """获取图片信息"""
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "ratio": f"{image.width / image.height:.2f}",
        }
