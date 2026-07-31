"""统一本地日志系统。

设计约定：
- INFO：正常操作（请求、上传、任务提交、命令执行）
- WARNING：结构轻微异常（依赖缺失降级、属性计算失败）
- ERROR：计算失败、未捕获异常
- 文件按日期轮转：logs/cadd.log.{YYYY-MM-DD}
- 每条日志记录：操作人、任务 ID、输入文件名、软件执行命令、报错堆栈
- 文件日志为 JSON 行，前端日志查看页可直接解析展示
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any


_operator_var: ContextVar[str] = ContextVar("cadd_operator", default="local-user")
_task_var: ContextVar[str] = ContextVar("cadd_task_id", default="")
_input_var: ContextVar[str] = ContextVar("cadd_input_file", default="")


def bind_log_context(
    *,
    operator: str | None = None,
    task_id: str | None = None,
    input_file: str | None = None,
) -> list[Token]:
    """绑定当前请求/任务的日志上下文，返回用于恢复的 token 列表。"""

    tokens: list[Token] = []
    if operator is not None:
        tokens.append(_operator_var.set(operator))
    if task_id is not None:
        tokens.append(_task_var.set(task_id))
    if input_file is not None:
        tokens.append(_input_var.set(input_file))
    return tokens


def reset_log_context(tokens: list[Token]) -> None:
    """恢复日志上下文。"""

    for token in reversed(tokens):
        token.var.reset(token)


def get_log_context() -> dict[str, str]:
    """返回当前日志上下文字典。"""

    return {
        "operator": _operator_var.get(),
        "task_id": _task_var.get(),
        "input_file": _input_var.get(),
    }


class JsonLogFormatter(logging.Formatter):
    """将日志记录格式化为 JSON 行，便于前端解析与后续工具对接。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created).isoformat(timespec="seconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "operator": getattr(record, "operator", None) or _operator_var.get(),
            "task_id": getattr(record, "task_id", None) or _task_var.get(),
            "input_file": getattr(record, "input_file", None) or _input_var.get(),
            "command": getattr(record, "command", None),
            "source_file": getattr(record, "source_file", None),
            "error_stack": "",
        }
        if record.exc_info:
            payload["error_stack"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO", log_dir: Path | None = None) -> logging.Logger:
    """初始化应用日志：控制台可读文本 + 文件 JSON 行（按日期轮转）。"""

    logger = logging.getLogger("cadd")
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())
    logger.propagate = False

    text_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(text_formatter)
    logger.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = TimedRotatingFileHandler(
            log_dir / "cadd.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setFormatter(JsonLogFormatter())
        logger.addHandler(file_handler)

    return logger


def iter_log_entries(
    log_dir: Path,
    date: str | None = None,
    level: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """读取指定日期（默认今天）的 JSON 行日志，按时间倒序返回。"""

    target_date = date or datetime.now().strftime("%Y-%m-%d")
    candidates = [log_dir / f"cadd.log.{target_date}"]
    if target_date == datetime.now().strftime("%Y-%m-%d"):
        candidates.append(log_dir / "cadd.log")

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                entry = {"time": target_date, "level": "INFO", "logger": "file", "message": line}
            key = json.dumps(entry, ensure_ascii=False, sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            entries.append(entry)

    if level:
        level = level.upper()
        entries = [entry for entry in entries if str(entry.get("level", "")).upper() == level]
    entries.sort(key=lambda item: str(item.get("time", "")), reverse=True)
    return entries[:limit]
