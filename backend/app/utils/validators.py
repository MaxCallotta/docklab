"""输入校验工具函数。"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.constants import ALLOWED_UPLOAD_EXTENSIONS, PDB_ID_PATTERN
from app.core.exceptions import FileTypeInvalidError, RequestParamError


def validate_extension(filename: str, *, allowed: dict[str, str] | None = None) -> str:
    """校验文件后缀，返回格式标识；失败抛出 FileTypeInvalidError。"""

    allowed = allowed or ALLOWED_UPLOAD_EXTENSIONS
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise FileTypeInvalidError(
            f"不支持的文件类型：{ext or '无后缀'}。支持格式：{', '.join(sorted(allowed))}"
        )
    return allowed[ext]


def validate_pdb_id(pdb_id: str) -> str:
    """校验 RCSB PDB ID 格式（如 1abc）。"""

    pdb_id = pdb_id.strip().lower()
    if not re.fullmatch(PDB_ID_PATTERN, pdb_id):
        raise RequestParamError(f"PDB ID 格式不正确：{pdb_id}。应为 4 位字符，首位为数字。")
    return pdb_id


def validate_positive_number(name: str, value: float | int | None) -> float:
    """校验数值必须大于 0。"""

    if value is None or float(value) <= 0:
        raise RequestParamError(f"参数 {name} 必须为正数，当前值：{value}")
    return float(value)


def sanitize_task_id(task_id: str) -> str:
    """校验任务 ID 只包含安全字符，防止路径穿越。"""

    if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", task_id):
        raise RequestParamError(f"非法任务 ID：{task_id}")
    return task_id
