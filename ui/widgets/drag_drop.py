"""
拖拽区域组件
"""
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class DragDropArea(QLabel):
    """拖拽区域"""

    files_dropped = pyqtSignal(list)

    def __init__(self, text: str = "拖拽文件到此处", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #4a9eff;
                background-color: #e8f4ff;
            }
        """)

        # 启用拖拽
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #4a9eff;
                    border-radius: 10px;
                    background-color: #e8f4ff;
                    color: #333;
                    font-size: 14px;
                }
            """)

    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #4a9eff;
                background-color: #e8f4ff;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #4a9eff;
                background-color: #e8f4ff;
            }
        """)

        urls = event.mimeData().urls()
        if urls:
            file_paths = [url.toLocalFile() for url in urls]
            self.files_dropped.emit(file_paths)
