"""
PDF转图片核心模块
使用PyMuPDF实现PDF到图片的转换
"""
import os
import fitz  # PyMuPDF
from PIL import Image
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """输出格式枚举"""
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    BMP = "bmp"
    TIFF = "tiff"


@dataclass
class ConvertOptions:
    """转换选项"""
    dpi: int = 300                    # DPI分辨率
    format: OutputFormat = OutputFormat.PNG  # 输出格式
    quality: int = 95                 # 图片质量(JPG)
    page_range: Optional[str] = None  # 页面范围，如 "1-5,8,10-12"
    grayscale: bool = False           # 灰度模式
    alpha: bool = False               # 是否保留透明通道(PNG)


@dataclass
class ConvertResult:
    """转换结果"""
    success: bool
    output_path: str
    page_num: int
    error_message: Optional[str] = None


class PDFConverter:
    """PDF转图片转换器"""

    def __init__(self):
        self._progress_callback: Optional[Callable[[int, int], None]] = None

    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def parse_page_range(self, page_range_str: str, total_pages: int) -> List[int]:
        """
        解析页面范围字符串
        例如: "1-5,8,10-12" -> [0,1,2,3,4,7,9,10,11] (0-indexed)
        """
        if not page_range_str or page_range_str.strip() == "":
            return list(range(total_pages))

        pages = set()
        parts = page_range_str.replace(" ", "").split(",")

        for part in parts:
            if "-" in part:
                start, end = part.split("-", 1)
                start = max(1, int(start))
                end = min(total_pages, int(end))
                pages.update(range(start - 1, end))
            else:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages.add(page - 1)

        return sorted(list(pages))

    def convert_single_page(
        self,
        pdf_path: str,
        page_num: int,
        output_path: str,
        options: ConvertOptions
    ) -> ConvertResult:
        """转换单页PDF为图片"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # 计算缩放比例
            zoom = options.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            # 获取像素图
            if options.alpha and options.format == OutputFormat.PNG:
                pix = page.get_pixmap(matrix=mat, alpha=True)
            else:
                pix = page.get_pixmap(matrix=mat, alpha=False)

            # 转换为PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 灰度模式
            if options.grayscale:
                img = img.convert("L")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 保存图片
            save_kwargs = {}
            if options.format in [OutputFormat.JPG, OutputFormat.JPEG]:
                save_kwargs["quality"] = options.quality
                save_kwargs["optimize"] = True
                # JPG不支持透明通道
                if img.mode == "RGBA":
                    img = img.convert("RGB")
            elif options.format == OutputFormat.PNG:
                save_kwargs["optimize"] = True

            img.save(output_path, **save_kwargs)
            doc.close()

            return ConvertResult(
                success=True,
                output_path=output_path,
                page_num=page_num + 1
            )

        except Exception as e:
            return ConvertResult(
                success=False,
                output_path=output_path,
                page_num=page_num + 1,
                error_message=str(e)
            )

    def convert_pdf(
        self,
        pdf_path: str,
        output_dir: str,
        options: ConvertOptions,
        filename_template: str = "{name}_page{page:03d}"
    ) -> List[ConvertResult]:
        """
        转换整个PDF文件为图片

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            options: 转换选项
            filename_template: 文件名模板，支持 {name}, {page} 变量

        Returns:
            转换结果列表
        """
        results = []

        try:
            doc = fitz.open(pdf_path)
            total_pages = doc.page_count
            doc.close()

            # 解析页面范围
            pages = self.parse_page_range(options.page_range, total_pages)

            if not pages:
                return [ConvertResult(
                    success=False,
                    output_path="",
                    page_num=0,
                    error_message="没有有效的页面范围"
                )]

            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

            for i, page_idx in enumerate(pages):
                # 生成输出文件名
                filename = filename_template.format(
                    name=pdf_name,
                    page=page_idx + 1
                )
                output_path = os.path.join(
                    output_dir,
                    f"{filename}.{options.format.value}"
                )

                # 转换页面
                result = self.convert_single_page(
                    pdf_path, page_idx, output_path, options
                )
                results.append(result)

                # 更新进度
                if self._progress_callback:
                    self._progress_callback(i + 1, len(pages))

        except Exception as e:
            results.append(ConvertResult(
                success=False,
                output_path="",
                page_num=0,
                error_message=f"打开PDF文件失败: {str(e)}"
            ))

        return results

    def get_pdf_info(self, pdf_path: str) -> dict:
        """获取PDF文件信息"""
        try:
            doc = fitz.open(pdf_path)
            info = {
                "path": pdf_path,
                "name": os.path.basename(pdf_path),
                "pages": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "size": os.path.getsize(pdf_path),
            }

            # 获取第一页尺寸
            if doc.page_count > 0:
                page = doc[0]
                rect = page.rect
                info["page_width"] = rect.width
                info["page_height"] = rect.height

            doc.close()
            return info

        except Exception as e:
            return {
                "path": pdf_path,
                "name": os.path.basename(pdf_path),
                "error": str(e)
            }

    def render_page_preview(
        self,
        pdf_path: str,
        page_num: int,
        max_width: int = 400,
        max_height: int = 600
    ) -> Optional[Image.Image]:
        """渲染PDF页面预览图"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # 计算适合的缩放比例
            rect = page.rect
            scale_x = max_width / rect.width
            scale_y = max_height / rect.height
            scale = min(scale_x, scale_y)

            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()

            return img

        except Exception:
            return None
