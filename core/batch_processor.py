"""
批量处理模块
支持多文件并发处理
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Callable
from dataclasses import dataclass, field
from queue import Queue

from .converter import PDFConverter, ConvertOptions, ConvertResult


@dataclass
class BatchTask:
    """批量处理任务"""
    pdf_path: str
    output_dir: str
    options: ConvertOptions
    results: List[ConvertResult] = field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, failed
    progress: int = 0
    total_pages: int = 0


@dataclass
class BatchProgress:
    """批量处理进度"""
    total_files: int
    completed_files: int
    current_file: str
    current_page: int
    total_pages: int
    overall_progress: float  # 0-100


class BatchProcessor:
    """批量处理器"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.converter = PDFConverter()
        self._tasks: List[BatchTask] = []
        self._running = False
        self._paused = False
        self._cancel_flag = False
        self._lock = threading.Lock()

        # 回调函数
        self._progress_callback: Optional[Callable[[BatchProgress], None]] = None
        self._file_complete_callback: Optional[Callable[[BatchTask], None]] = None
        self._all_complete_callback: Optional[Callable[[List[BatchTask]], None]] = None

    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """设置进度回调"""
        self._progress_callback = callback

    def set_file_complete_callback(self, callback: Callable[[BatchTask], None]):
        """设置单文件完成回调"""
        self._file_complete_callback = callback

    def set_all_complete_callback(self, callback: Callable[[List[BatchTask]], None]):
        """设置全部完成回调"""
        self._all_complete_callback = callback

    def add_task(self, pdf_path: str, output_dir: str, options: ConvertOptions) -> BatchTask:
        """添加处理任务"""
        task = BatchTask(
            pdf_path=pdf_path,
            output_dir=output_dir,
            options=options
        )
        self._tasks.append(task)
        return task

    def add_tasks(self, pdf_paths: List[str], output_dir: str, options: ConvertOptions) -> List[BatchTask]:
        """批量添加任务"""
        tasks = []
        for path in pdf_paths:
            task = self.add_task(path, output_dir, options)
            tasks.append(task)
        return tasks

    def remove_task(self, task: BatchTask):
        """移除任务"""
        with self._lock:
            if task in self._tasks and task.status == "pending":
                self._tasks.remove(task)

    def clear_tasks(self):
        """清空所有待处理任务"""
        with self._lock:
            self._tasks = [t for t in self._tasks if t.status == "processing"]

    def get_tasks(self) -> List[BatchTask]:
        """获取所有任务"""
        return self._tasks.copy()

    def pause(self):
        """暂停处理"""
        self._paused = True

    def resume(self):
        """恢复处理"""
        self._paused = False

    def cancel(self):
        """取消处理"""
        self._cancel_flag = True
        self._paused = False

    def _process_task(self, task: BatchTask) -> BatchTask:
        """处理单个任务"""
        if self._cancel_flag:
            task.status = "failed"
            task.results = [ConvertResult(
                success=False,
                output_path="",
                page_num=0,
                error_message="任务已取消"
            )]
            return task

        # 等待恢复
        while self._paused and not self._cancel_flag:
            threading.Event().wait(0.1)

        if self._cancel_flag:
            task.status = "failed"
            return task

        task.status = "processing"

        def progress_callback(current: int, total: int):
            task.progress = current
            task.total_pages = total

            if self._progress_callback:
                total_files = len(self._tasks)
                completed_files = sum(1 for t in self._tasks if t.status == "completed")

                # 计算总体进度
                file_weight = 1.0 / total_files if total_files > 0 else 0
                page_progress = current / total if total > 0 else 0
                overall = (completed_files * file_weight + page_progress * file_weight) * 100

                progress = BatchProgress(
                    total_files=total_files,
                    completed_files=completed_files,
                    current_file=os.path.basename(task.pdf_path),
                    current_page=current,
                    total_pages=total,
                    overall_progress=min(overall, 100)
                )
                self._progress_callback(progress)

        self.converter.set_progress_callback(progress_callback)
        task.results = self.converter.convert_pdf(
            task.pdf_path,
            task.output_dir,
            task.options
        )

        # 检查是否全部成功
        all_success = all(r.success for r in task.results)
        task.status = "completed" if all_success else "failed"

        if self._file_complete_callback:
            self._file_complete_callback(task)

        return task

    def start(self) -> List[BatchTask]:
        """开始批量处理（同步）"""
        self._running = True
        self._cancel_flag = False
        self._paused = False

        pending_tasks = [t for t in self._tasks if t.status == "pending"]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_task, task): task
                for task in pending_tasks
            }

            for future in as_completed(futures):
                if self._cancel_flag:
                    break
                future.result()

        self._running = False

        if self._all_complete_callback:
            self._all_complete_callback(self._tasks)

        return self._tasks

    def start_async(self):
        """异步开始批量处理"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def progress_summary(self) -> dict:
        """获取进度摘要"""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.status == "completed")
        failed = sum(1 for t in self._tasks if t.status == "failed")
        pending = sum(1 for t in self._tasks if t.status == "pending")
        processing = sum(1 for t in self._tasks if t.status == "processing")

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": processing,
            "progress": (completed / total * 100) if total > 0 else 0
        }
