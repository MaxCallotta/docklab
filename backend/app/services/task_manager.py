"""任务管理持久化模块（核心模块 4）。

职责：
- 每个任务唯一 ID 与独立目录（input/prepared/work/output/export）；
- meta.json 原子持久化任务状态：queued/running/completed/failed；
- 历史查询、失败任务重启、批量删除、全结果打包下载；
- 全部数据仅存储本地磁盘（默认数据目录 tasks）。
"""

from __future__ import annotations

import shutil
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from app.core.config import Settings, get_settings
from app.core.constants import TaskDirName, TaskStatus
from app.core.exceptions import TaskNotFoundError, TaskStateError
from app.core.paths import get_paths
from app.models.task import TaskRecord
from app.utils.atomic_json import read_json, write_json_atomic
from app.utils.file_utils import ensure_dir, make_zip, save_bytes
from app.utils.validators import sanitize_task_id


class TaskManager:
    """本地 JSON 任务管理器的单机实现。"""

    def __init__(
        self,
        tasks_root: Path | str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.tasks_root = Path(tasks_root) if tasks_root else get_paths().tasks_dir
        ensure_dir(self.tasks_root)
        self._lock = threading.RLock()

    # ---------- 任务生命周期 ----------

    def create_task(
        self,
        name: str,
        *,
        engine_id: str = "",
        params: dict[str, Any] | None = None,
        input_files: dict[str, str] | None = None,
    ) -> TaskRecord:
        """创建任务：生成 UUID、初始化目录、写入 meta.json。"""

        task_id = uuid.uuid4().hex
        task_dir = self.tasks_root / task_id
        for sub in (
            TaskDirName.INPUT,
            TaskDirName.PREPARED,
            TaskDirName.WORK,
            TaskDirName.OUTPUT,
            TaskDirName.EXPORT,
        ):
            ensure_dir(task_dir / sub)

        record = TaskRecord(
            task_id=task_id,
            name=name,
            status=TaskStatus.QUEUED,
            engine_id=engine_id,
            params=params or {},
            input_files=input_files or {},
        )
        self._save(record)
        return record

    def get_task(self, task_id: str) -> TaskRecord:
        """按 ID 读取任务记录。"""

        sanitize_task_id(task_id)
        meta_path = self._meta_path(task_id)
        data = read_json(meta_path)
        if not data:
            raise TaskNotFoundError(f"任务不存在：{task_id}")
        return TaskRecord.from_dict(data)

    def list_tasks(self, status: str | None = None) -> list[TaskRecord]:
        """查询历史任务，可按状态过滤，按创建时间倒序。"""

        records: list[TaskRecord] = []
        for meta_path in sorted(self.tasks_root.glob("*/meta.json"), reverse=True):
            data = read_json(meta_path)
            if not data:
                continue
            record = TaskRecord.from_dict(data)
            if status and record.status != status:
                continue
            records.append(record)
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records

    def update_status(
        self,
        task_id: str,
        status: str,
        *,
        error_code: str = "",
        error_message: str = "",
        result_summary: dict[str, Any] | None = None,
        output_files: dict[str, str] | None = None,
        warnings: list[str] | None = None,
    ) -> TaskRecord:
        """更新任务状态与结果摘要。"""

        with self._lock:
            record = self.get_task(task_id)
            record.status = status
            record.updated_at = datetime.now().isoformat(timespec="seconds")
            record.error_code = error_code
            record.error_message = error_message
            if result_summary is not None:
                record.result_summary = result_summary
            if output_files is not None:
                record.output_files = {**record.output_files, **output_files}
            if warnings is not None:
                record.warnings = warnings
            self._save(record)
            return record

    def update_params(self, task_id: str, params: dict[str, Any]) -> TaskRecord:
        """持久化对接参数，供失败重启/重新运行复用。"""

        with self._lock:
            record = self.get_task(task_id)
            record.params = params
            record.updated_at = datetime.now().isoformat(timespec="seconds")
            self._save(record)
            return record

    def restart_task(self, task_id: str) -> TaskRecord:
        """重启失败任务：状态 failed -> queued，清空错误信息。"""

        with self._lock:
            record = self.get_task(task_id)
            if record.status not in (TaskStatus.FAILED, TaskStatus.COMPLETED):
                raise TaskStateError(
                    f"仅失败或已完成任务可重启，当前状态：{record.status}"
                )
            record.status = TaskStatus.QUEUED
            record.updated_at = datetime.now().isoformat(timespec="seconds")
            record.error_code = ""
            record.error_message = ""
            self._save(record)
            return record

    def delete_task(self, task_id: str) -> None:
        """删除任务：运行中任务禁止删除。"""

        with self._lock:
            record = self.get_task(task_id)
            if record.status == TaskStatus.RUNNING:
                raise TaskStateError("运行中的任务不允许删除，请等待完成或停止。")
            task_dir = self.tasks_root / task_id
            resolved = task_dir.resolve()
            if not resolved.is_relative_to(self.tasks_root.resolve()):
                raise TaskStateError(f"任务目录越界，已拒绝删除：{task_dir}")
            if task_dir.exists():
                shutil.rmtree(resolved)

    def delete_tasks(self, task_ids: Iterable[str]) -> int:
        """批量删除任务，返回成功删除数量。"""

        deleted = 0
        for task_id in task_ids:
            try:
                self.delete_task(task_id)
                deleted += 1
            except TaskNotFoundError:
                continue
        return deleted

    def export_task(self, task_id: str, export_dir: Path | str | None = None) -> Path:
        """将任务全部结果打包为 zip，返回压缩包路径。"""

        record = self.get_task(task_id)
        task_dir = self.tasks_root / task_id
        target_dir = Path(export_dir) if export_dir else get_paths().exports_dir
        zip_path = make_zip(task_dir, target_dir / f"{task_id}.zip")
        record.output_files["export_zip"] = str(zip_path)
        self._save(record)
        return zip_path

    # ---------- 文件落盘 ----------

    def save_input_file(self, task_id: str, filename: str, data: bytes) -> Path:
        """保存原始上传文件到任务 input 目录。"""

        record = self.get_task(task_id)
        task_dir = self.tasks_root / task_id
        dst = save_bytes(data, task_dir / TaskDirName.INPUT / filename)
        record.input_files[filename] = str(dst)
        self._save(record)
        return dst

    def task_dir(self, task_id: str) -> Path:
        """返回任务根目录。"""

        sanitize_task_id(task_id)
        return self.tasks_root / task_id

    # ---------- 内部工具 ----------

    def _meta_path(self, task_id: str) -> Path:
        return self.tasks_root / task_id / "meta.json"

    def _save(self, record: TaskRecord) -> None:
        write_json_atomic(self._meta_path(record.task_id), record.to_dict())
