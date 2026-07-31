"""JSON 原子读写工具。

采用「临时文件写入 + os.replace 原子替换」策略，
避免任务中途断电/崩溃损坏任务记录。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: Path | str, default: Any = None) -> Any:
    """读取 JSON 文件；文件不存在或损坏时返回 default。"""

    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def write_json_atomic(path: Path | str, data: Any, *, indent: int = 2) -> Path:
    """原子写入 JSON 文件，返回目标路径。"""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=indent)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
    return path
