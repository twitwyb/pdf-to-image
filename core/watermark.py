"""
水印功能模块
支持文字水印和图片水印
"""
import os
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class WatermarkPosition(Enum):
    """水印位置"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    TILE = "tile"  # 平铺


@dataclass
class TextWatermarkOptions:
    """文字水印选项"""
    text: str = "水印"
    font_size: int = 36
    font_color: Tuple[int, int, int] = (128, 128, 128)  # 灰色
    opacity: int = 128  # 0-255
    position: WatermarkPosition = WatermarkPosition.CENTER
    rotation: int = 30  # 旋转角度
    font_path: Optional[str] = None  # 自定义字体路径
    margin: int = 20  # 边距


@dataclass
class ImageWatermarkOptions:
    """图片水印选项"""
    watermark_path: str = ""
    opacity: int = 128  # 0-255
    position: WatermarkPosition = WatermarkPosition.CENTER
    scale: float = 0.2  # 缩放比例（相对于原图）
    margin: int = 20


class WatermarkProcessor:
    """水印处理器"""

    @staticmethod
    def get_position_coords(
        img_size: Tuple[int, int],
        wm_size: Tuple[int, int],
        position: WatermarkPosition,
        margin: int = 20
    ) -> Tuple[int, int]:
        """计算水印位置坐标"""
        img_w, img_h = img_size
        wm_w, wm_h = wm_size

        positions = {
            WatermarkPosition.TOP_LEFT: (margin, margin),
            WatermarkPosition.TOP_CENTER: ((img_w - wm_w) // 2, margin),
            WatermarkPosition.TOP_RIGHT: (img_w - wm_w - margin, margin),
            WatermarkPosition.CENTER: ((img_w - wm_w) // 2, (img_h - wm_h) // 2),
            WatermarkPosition.BOTTOM_LEFT: (margin, img_h - wm_h - margin),
            WatermarkPosition.BOTTOM_CENTER: ((img_w - wm_w) // 2, img_h - wm_h - margin),
            WatermarkPosition.BOTTOM_RIGHT: (img_w - wm_w - margin, img_h - wm_h - margin),
        }

        return positions.get(position, positions[WatermarkPosition.CENTER])

    @staticmethod
    def get_default_font(size: int) -> ImageFont.FreeTypeFont:
        """获取默认字体"""
        # 尝试加载系统中文字体
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",      # 宋体
            "C:/Windows/Fonts/simhei.ttf",      # 黑体
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
            "/System/Library/Fonts/PingFang.ttc",  # macOS
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue

        # 如果没有找到系统字体，使用默认字体
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()

    @staticmethod
    def add_text_watermark(
        image: Image.Image,
        options: TextWatermarkOptions
    ) -> Image.Image:
        """添加文字水印"""
        # 确保图片是RGBA模式
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 创建水印层
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)

        # 加载字体
        if options.font_path and os.path.exists(options.font_path):
            font = ImageFont.truetype(options.font_path, options.font_size)
        else:
            font = WatermarkProcessor.get_default_font(options.font_size)

        # 获取文字尺寸
        bbox = draw.textbbox((0, 0), options.text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 创建文字图片（用于旋转）
        text_img = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)
        color = (*options.font_color, options.opacity)
        text_draw.text((10, 10), options.text, font=font, fill=color)

        # 旋转文字
        if options.rotation != 0:
            text_img = text_img.rotate(options.rotation, expand=True, resample=Image.BICUBIC)

        if options.position == WatermarkPosition.TILE:
            # 平铺模式
            wm_w, wm_h = text_img.size
            spacing_x = int(wm_w * 1.5)
            spacing_y = int(wm_h * 2)

            for y in range(-wm_h, image.height + wm_h, spacing_y):
                for x in range(-wm_w, image.width + wm_w, spacing_x):
                    watermark_layer.paste(text_img, (x, y), text_img)
        else:
            # 单个水印
            pos = WatermarkProcessor.get_position_coords(
                image.size, text_img.size, options.position, options.margin
            )
            watermark_layer.paste(text_img, pos, text_img)

        # 合并图层
        return Image.alpha_composite(image, watermark_layer)

    @staticmethod
    def add_image_watermark(
        image: Image.Image,
        options: ImageWatermarkOptions
    ) -> Image.Image:
        """添加图片水印"""
        if not os.path.exists(options.watermark_path):
            raise FileNotFoundError(f"水印图片不存在: {options.watermark_path}")

        # 确保图片是RGBA模式
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 加载水印图片
        watermark = Image.open(options.watermark_path).convert("RGBA")

        # 缩放水印
        wm_w = int(image.width * options.scale)
        wm_h = int(watermark.height * (wm_w / watermark.width))
        watermark = watermark.resize((wm_w, wm_h), Image.LANCZOS)

        # 调整透明度
        if options.opacity < 255:
            alpha = watermark.split()[3]
            alpha = alpha.point(lambda p: int(p * options.opacity / 255))
            watermark.putalpha(alpha)

        # 创建水印层
        watermark_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))

        if options.position == WatermarkPosition.TILE:
            # 平铺模式
            spacing_x = int(wm_w * 1.5)
            spacing_y = int(wm_h * 1.5)

            for y in range(0, image.height, spacing_y):
                for x in range(0, image.width, spacing_x):
                    watermark_layer.paste(watermark, (x, y), watermark)
        else:
            # 单个水印
            pos = WatermarkProcessor.get_position_coords(
                image.size, watermark.size, options.position, options.margin
            )
            watermark_layer.paste(watermark, pos, watermark)

        # 合并图层
        return Image.alpha_composite(image, watermark_layer)

    @staticmethod
    def add_watermark_to_file(
        input_path: str,
        output_path: str,
        options: TextWatermarkOptions | ImageWatermarkOptions,
        is_image_watermark: bool = False
    ) -> bool:
        """为图片文件添加水印"""
        try:
            image = Image.open(input_path)

            if is_image_watermark:
                result = WatermarkProcessor.add_image_watermark(image, options)
            else:
                result = WatermarkProcessor.add_text_watermark(image, options)

            # 保存时转换为RGB（如果保存为JPG）
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                result = result.convert("RGB")

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result.save(output_path)
            return True

        except Exception as e:
            print(f"添加水印失败: {e}")
            return False
