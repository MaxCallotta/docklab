"""任务记录 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.core.constants import TaskStatus


def _now() -> str:
    """返回本地时间 ISO 字符串。"""

    return datetime.now().isoformat(timespec="seconds")


@dataclass
class TaskRecord:
    """本地 JSON 持久化的任务记录。"""

    task_id: str
    name: str
    status: str = TaskStatus.QUEUED
    engine_id: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    params: dict[str, Any] = field(default_factory=dict)
    input_files: dict[str, str] = field(default_factory=dict)
    output_files: dict[str, str] = field(default_factory=dict)
    error_code: str = ""
    error_message: str = ""
    result_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转为 JSON 可序列化字典。"""

        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status,
            "engine_id": self.engine_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "params": self.params,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "result_summary": self.result_summary,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskRecord":
        """从字典恢复任务记录。"""

        return cls(
            task_id=str(data.get("task_id", "")),
            name=str(data.get("name", "")),
            status=str(data.get("status", TaskStatus.QUEUED)),
            engine_id=str(data.get("engine_id", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
            params=dict(data.get("params") or {}),
            input_files=dict(data.get("input_files") or {}),
            output_files=dict(data.get("output_files") or {}),
            error_code=str(data.get("error_code", "")),
            error_message=str(data.get("error_message", "")),
            result_summary=dict(data.get("result_summary") or {}),
            warnings=list(data.get("warnings") or []),
        )
