# 📄 PDF转图片工具

一个功能强大、界面美观的PDF转图片桌面应用，基于 Python + PyQt6 + PyMuPDF 开发。

![Version](https://img.shields.io/badge/version-1.1-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## ✨ 功能特性

### 📄 PDF转图片
- 支持多种输出格式：**PNG、JPG、BMP、TIFF**
- 可调节 **DPI分辨率**（72/150/300/600/自定义）
- 支持选择**页面范围**（全部/自定义）
- 支持**灰度模式**和**透明通道**
- 实时**页面预览**
- 转换完成后**自动打开输出目录**

### 📚 批量处理
- 支持**多文件批量转换**
- **多线程并发**处理，速度更快
- 实时**进度显示**
- 支持**暂停/继续/取消**操作

### ✏️ 编辑功能

#### 🏷️ 水印
- **文字水印**：自定义文字、字体大小、颜色、透明度、旋转角度
- **图片水印**：支持PNG/JPG水印图片
- **平铺模式**：水印可平铺覆盖整张图片
- **多种位置**：居中、四角、自定义位置

#### ✂️ 裁剪
- **按比例裁剪**：16:9、4:3、1:1等常用比例
- **居中裁剪**：指定宽高居中裁剪
- **百分比裁剪**：按百分比裁剪四边

#### 🔗 合并
- **合并为PDF**：多张图片合并为一个PDF文件
- **水平拼接**：多张图片水平拼接
- **垂直拼接**：多张图片垂直拼接
- **网格拼接**：多张图片按网格排列

### 🔍 OCR识别
- 支持**中文+英文**识别
- 可调节**识别精度**
- 支持**图片预处理**（灰度化、二值化）
- 识别结果可**导出为TXT/Word**

## 📸 界面预览

程序支持**浅色**和**深色**两种主题，可通过 `视图 → 主题` 切换。

### 主要界面
- **PDF转图片**：左侧文件列表+预览，右侧设置面板
- **批量处理**：文件表格+批量设置+进度控制
- **编辑功能**：水印/裁剪/合并三个子标签页
- **OCR识别**：文件选择+识别设置+结果导出

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/pdf-to-image.git
cd pdf-to-image

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

### 3. 使用步骤

#### PDF转图片
1. 点击 **「添加文件」** 或直接 **拖拽PDF文件** 到窗口
2. 设置输出格式、DPI、页面范围
3. 选择输出目录
4. 点击 **「开始转换」**

#### 批量处理
1. 添加多个PDF文件或整个文件夹
2. 统一设置输出参数
3. 点击 **「开始批量处理」**
4. 可随时暂停/继续/取消

#### 添加水印
1. 切换到 **「编辑功能」** 标签页
2. 选择 **「水印」** 子标签
3. 设置水印类型（文字/图片）、位置、透明度
4. 点击 **「执行」**

#### 图片裁剪
1. 选择 **「裁剪」** 子标签
2. 选择裁剪模式（按比例/居中/百分比）
3. 设置裁剪参数
4. 点击 **「执行」**

#### 图片合并
1. 选择 **「合并」** 子标签
2. 选择合并模式（PDF/水平/垂直/网格）
3. 点击 **「执行」**

#### OCR识别
1. 切换到 **「OCR识别」** 标签页
2. 打开PDF或图片文件
3. 选择识别语言
4. 点击 **「开始识别」**
5. 导出识别结果

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开PDF文件 |
| `Ctrl+Shift+O` | 打开文件夹 |
| `Ctrl+,` | 打开设置 |
| `Ctrl+Q` | 退出程序 |
| `F1` | 使用帮助 |

## 📁 项目结构

```
PDF转图片/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖列表
├── README.md              # 说明文档
├── .gitignore             # Git忽略文件
├── ui/                    # 界面模块
│   ├── main_window.py     # 主窗口
│   ├── convert_tab.py     # 转换标签页
│   ├── batch_tab.py       # 批量处理标签页
│   ├── edit_tab.py        # 编辑功能标签页
│   ├── ocr_tab.py         # OCR识别标签页
│   └── widgets/           # 自定义组件
│       └── drag_drop.py   # 拖拽组件
├── core/                  # 核心功能
│   ├── converter.py       # PDF转图片引擎
│   ├── batch_processor.py # 批量处理器
│   ├── watermark.py       # 水印功能
│   ├── cropper.py         # 裁剪功能
│   ├── merger.py          # 合并功能
│   └── ocr_engine.py      # OCR引擎
└── utils/                 # 工具模块
    ├── config.py          # 配置管理
    ├── logger.py          # 日志工具
    └── file_utils.py      # 文件工具
```

## 📦 依赖包

| 包名 | 版本 | 用途 |
|------|------|------|
| PyQt6 | >=6.5.0 | GUI框架 |
| PyMuPDF | >=1.23.0 | PDF处理 |
| Pillow | >=10.0.0 | 图像处理 |
| pytesseract | >=0.3.10 | OCR识别 |
| python-docx | >=0.8.11 | Word文档导出 |

## 🔧 OCR配置（可选）

OCR功能需要安装Tesseract OCR引擎：

### Windows
1. 下载安装包：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装时勾选 **Chinese Simplified** 语言包
3. 将安装目录（如 `C:\Program Files\Tesseract-OCR`）添加到系统PATH

### macOS
```bash
brew install tesseract
brew install tesseract-lang  # 安装语言包
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-chi-sim  # 简体中文
sudo apt install tesseract-ocr-chi-tra  # 繁体中文
```

## 🛠️ 打包为EXE

```bash
# 安装PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --windowed --icon=icon.ico main.py

# 生成的exe在dist目录下
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF处理库
- [Pillow](https://pillow.readthedocs.io/) - 图像处理库
- [Tesseract](https://github.com/tesseract-ocr/tesseract) - OCR引擎

---

**Made with ❤️ by PDF Converter Team**
