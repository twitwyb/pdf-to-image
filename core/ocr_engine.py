"""
OCR识别引擎模块
基于pytesseract实现文字识别
"""
import os
from PIL import Image
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class OCRLanguage(Enum):
    """OCR语言"""
    CHINESE_SIMPLIFIED = "chi_sim"
    CHINESE_TRADITIONAL = "chi_tra"
    ENGLISH = "eng"
    CHINESE_ENG = "chi_sim+eng"
    JAPANESE = "jpn"
    KOREAN = "kor"


@dataclass
class OCROptions:
    """OCR选项"""
    language: OCRLanguage = OCRLanguage.CHINESE_ENG
    preprocess: bool = True  # 是否预处理图片
    grayscale: bool = True  # 灰度化
    threshold: bool = True  # 二值化
    threshold_value: int = 128  # 二值化阈值
    dpi: int = 300  # DPI


@dataclass
class OCRResult:
    """OCR识别结果"""
    success: bool
    text: str
    confidence: float
    words: List[dict]  # 包含位置信息的单词列表
    error_message: Optional[str] = None


class OCREngine:
    """OCR识别引擎"""

    def __init__(self):
        self._tesseract_available = False
        self._check_tesseract()

    def _check_tesseract(self):
        """检查tesseract是否可用"""
        try:
            import pytesseract
            # 尝试获取版本
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            self._tesseract_available = False

    @property
    def is_available(self) -> bool:
        """检查OCR是否可用"""
        return self._tesseract_available

    def preprocess_image(
        self,
        image: Image.Image,
        options: OCROptions
    ) -> Image.Image:
        """预处理图片以提高OCR准确率"""
        # 转换为RGB
        if image.mode == "RGBA":
            bg = Image.new("RGB", image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 灰度化
        if options.grayscale:
            image = image.convert("L")

        # 二值化
        if options.threshold and image.mode == "L":
            image = image.point(lambda p: 255 if p > options.threshold_value else 0)

        return image

    def recognize_text(
        self,
        image: Image.Image,
        options: OCROptions
    ) -> OCRResult:
        """识别图片中的文字"""
        if not self._tesseract_available:
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                words=[],
                error_message="Tesseract未安装或不可用。请安装Tesseract OCR。"
            )

        try:
            import pytesseract

            # 预处理图片
            if options.preprocess:
                processed_image = self.preprocess_image(image, options)
            else:
                processed_image = image

            # 获取语言代码
            lang = options.language.value

            # 识别文字
            text = pytesseract.image_to_string(processed_image, lang=lang)

            # 获取详细信息（包含置信度和位置）
            data = pytesseract.image_to_data(
                processed_image,
                lang=lang,
                output_type=pytesseract.Output.DICT
            )

            # 计算平均置信度
            confidences = [
                int(c) for c, t in zip(data['conf'], data['text'])
                if int(c) > 0 and t.strip()
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # 构建单词列表
            words = []
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    words.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                    })

            return OCRResult(
                success=True,
                text=text.strip(),
                confidence=avg_confidence,
                words=words
            )

        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                words=[],
                error_message=f"OCR识别失败: {str(e)}"
            )

    def recognize_file(
        self,
        file_path: str,
        options: OCROptions
    ) -> OCRResult:
        """识别图片文件中的文字"""
        try:
            image = Image.open(file_path)
            return self.recognize_text(image, options)
        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                words=[],
                error_message=f"打开文件失败: {str(e)}"
            )

    def recognize_pdf_page(
        self,
        pdf_path: str,
        page_num: int,
        options: OCROptions
    ) -> OCRResult:
        """识别PDF页面中的文字"""
        try:
            import fitz

            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # 渲染页面为图片
            zoom = options.dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()

            return self.recognize_text(image, options)

        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                confidence=0,
                words=[],
                error_message=f"处理PDF页面失败: {str(e)}"
            )

    @staticmethod
    def save_as_text(text: str, output_path: str) -> bool:
        """保存识别结果为文本文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"保存文本失败: {e}")
            return False

    @staticmethod
    def save_as_docx(text: str, output_path: str) -> bool:
        """保存识别结果为Word文档"""
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.enum.text import WD_LINE_SPACING

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            doc = Document()

            # 设置默认字体
            style = doc.styles['Normal']
            font = style.font
            font.name = '宋体'
            font.size = Pt(12)

            # 添加文本
            paragraphs = text.split('\n')
            for para_text in paragraphs:
                if para_text.strip():
                    para = doc.add_paragraph(para_text)
                    para.paragraph_format.line_spacing = 1.5

            doc.save(output_path)
            return True

        except Exception as e:
            print(f"保存Word文档失败: {e}")
            return False
