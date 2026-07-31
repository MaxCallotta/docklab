"""本地存储服务：任务目录管理与上传文件落盘。"""

from __future__ import annotations

from pathlib import Path

from app.core.constants import TaskDirName
from app.utils.file_utils import ensure_dir


class StorageService:
    """提供任务目录内各子目录的稳定入口。"""

    @staticmethod
    def input_dir(task_dir: Path) -> Path:
        """原始上传文件目录。"""

        return ensure_dir(task_dir / TaskDirName.INPUT)

    @staticmethod
    def prepared_dir(task_dir: Path) -> Path:
        """预处理产物目录。"""

        return ensure_dir(task_dir / TaskDirName.PREPARED)

    @staticmethod
    def work_dir(task_dir: Path) -> Path:
        """中间文件/引擎日志目录。"""

        return ensure_dir(task_dir / TaskDirName.WORK)

    @staticmethod
    def output_dir(task_dir: Path) -> Path:
        """最终结果目录。"""

        return ensure_dir(task_dir / TaskDirName.OUTPUT)

    @staticmethod
    def export_dir(task_dir: Path) -> Path:
        """导出目录。"""

        return ensure_dir(task_dir / TaskDirName.EXPORT)
