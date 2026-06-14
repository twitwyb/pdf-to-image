"""
配置管理模块
"""
import os
import json
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """应用配置"""
    # 窗口设置
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False

    # 默认转换设置
    default_dpi: int = 300
    default_format: str = "png"
    default_quality: int = 95

    # 默认输出目录
    default_output_dir: str = ""

    # 批量处理设置
    max_workers: int = 4

    # OCR设置
    ocr_language: str = "chi_sim+eng"
    ocr_dpi: int = 300

    # 界面设置
    theme: str = "light"
    font_size: int = 10
    language: str = "zh_CN"


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = config_dir
        else:
            # 使用用户目录下的配置文件夹
            self.config_dir = os.path.join(os.path.expanduser("~"), ".pdf_converter")

        self.config_file = os.path.join(self.config_dir, "config.json")
        self.config = AppConfig()

        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)

        # 加载配置
        self.load()

    def load(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.config, key):
                            setattr(self.config, key, value)
        except Exception as e:
            print(f"加载配置失败: {e}")

    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()

    def reset(self):
        """重置为默认配置"""
        self.config = AppConfig()
        self.save()

    def get_recent_files(self) -> list:
        """获取最近打开的文件"""
        recent_file = os.path.join(self.config_dir, "recent.json")
        try:
            if os.path.exists(recent_file):
                with open(recent_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def add_recent_file(self, file_path: str, max_recent: int = 20):
        """添加到最近文件列表"""
        recent = self.get_recent_files()

        # 移除已存在的记录
        if file_path in recent:
            recent.remove(file_path)

        # 添加到开头
        recent.insert(0, file_path)

        # 限制数量
        recent = recent[:max_recent]

        # 保存
        recent_file = os.path.join(self.config_dir, "recent.json")
        try:
            with open(recent_file, 'w', encoding='utf-8') as f:
                json.dump(recent, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存最近文件列表失败: {e}")

    def get_window_geometry(self) -> Optional[dict]:
        """获取窗口位置和大小"""
        geo_file = os.path.join(self.config_dir, "geometry.json")
        try:
            if os.path.exists(geo_file):
                with open(geo_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def save_window_geometry(self, geometry: dict):
        """保存窗口位置和大小"""
        geo_file = os.path.join(self.config_dir, "geometry.json")
        try:
            with open(geo_file, 'w', encoding='utf-8') as f:
                json.dump(geometry, f)
        except Exception as e:
            print(f"保存窗口位置失败: {e}")
