"""
文件工具模块
"""
import os
import shutil
from typing import List, Optional
from pathlib import Path


def get_file_size_str(size_bytes: int) -> str:
    """将文件大小转换为可读字符串"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_unique_filename(file_path: str) -> str:
    """获取唯一的文件名（如果文件已存在则添加数字后缀）"""
    if not os.path.exists(file_path):
        return file_path

    base, ext = os.path.splitext(file_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


def ensure_dir(dir_path: str):
    """确保目录存在"""
    os.makedirs(dir_path, exist_ok=True)


def get_pdf_files(dir_path: str) -> List[str]:
    """获取目录中的PDF文件"""
    pdf_files = []
    if os.path.isdir(dir_path):
        for file in os.listdir(dir_path):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(dir_path, file))
    return sorted(pdf_files)


def get_image_files(dir_path: str) -> List[str]:
    """获取目录中的图片文件"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
    image_files = []
    if os.path.isdir(dir_path):
        for file in os.listdir(dir_path):
            if Path(file).suffix.lower() in image_extensions:
                image_files.append(os.path.join(dir_path, file))
    return sorted(image_files)


def is_pdf_file(file_path: str) -> bool:
    """检查是否为PDF文件"""
    return file_path.lower().endswith('.pdf')


def is_image_file(file_path: str) -> bool:
    """检查是否为图片文件"""
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions


def get_output_path(
    input_path: str,
    output_dir: str,
    suffix: str = "",
    new_ext: Optional[str] = None
) -> str:
    """生成输出文件路径"""
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)

    if new_ext:
        ext = new_ext
    if suffix:
        name = f"{name}_{suffix}"

    output_path = os.path.join(output_dir, name + ext)
    return get_unique_filename(output_path)


def clean_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    return filename


def copy_file(src: str, dst: str) -> bool:
    """复制文件"""
    try:
        ensure_dir(os.path.dirname(dst))
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"复制文件失败: {e}")
        return False


def move_file(src: str, dst: str) -> bool:
    """移动文件"""
    try:
        ensure_dir(os.path.dirname(dst))
        shutil.move(src, dst)
        return True
    except Exception as e:
        print(f"移动文件失败: {e}")
        return False


def delete_file(file_path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False


def get_file_info(file_path: str) -> dict:
    """获取文件信息"""
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "size_str": get_file_size_str(stat.st_size),
            "modified": stat.st_mtime,
            "extension": Path(file_path).suffix.lower(),
        }
    except Exception as e:
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "error": str(e)
        }
