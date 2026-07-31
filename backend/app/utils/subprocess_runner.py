"""跨平台子进程封装。

核心职责：
- 统一校验可执行程序是否存在；
- 捕获超时、退出码、stderr；
- 将原始终端输出翻译为面向科研用户的友好提示；
- 支持 stdin 输入（如 SMILES 字符串）。
"""

from __future__ import annotations

import os
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import EngineExecError, EngineNotFoundError


logger = logging.getLogger("cadd.exec")


@dataclass
class ProcessResult:
    """子进程执行结果。"""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float = 0.0
    ok: bool = True


def resolve_executable(executable: str | Path | None) -> str:
    """解析可执行程序：支持绝对路径或 PATH 探测。"""

    if not executable:
        raise EngineNotFoundError("未配置可执行程序路径，请检查环境变量或数据目录 config/engines.json")

    path = Path(executable)
    if path.exists():
        return str(path)
    found = shutil.which(str(executable))
    if found:
        return found
    raise EngineNotFoundError(f"未找到可执行程序：{executable}，请检查安装路径与 PATH 环境变量")


def run_command(
    command: list[str],
    *,
    cwd: Path | str | None = None,
    timeout: int = 3600,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
    friendly_name: str = "计算软件",
) -> ProcessResult:
    """执行外部命令并返回标准化结果；失败时抛出 EngineExecError。"""

    if not command:
        raise EngineExecError("空命令不允许执行")

    executable = resolve_executable(command[0])
    full_command = [executable, *command[1:]]
    started = time.monotonic()
    command_text = " ".join(full_command)
    logger.info(
        "exec command=%s cwd=%s timeout=%s",
        command_text,
        cwd,
        timeout,
        extra={"command": command_text},
    )

    try:
        proc = subprocess.run(
            full_command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            input=input_text,
            env={**os.environ, **(env or {})} if env else None,
        )
    except FileNotFoundError as exc:
        logger.error("exec failed executable_not_found=%s", executable, extra={"command": command_text})
        raise EngineNotFoundError(f"无法启动 {friendly_name}：{executable}") from exc
    except subprocess.TimeoutExpired as exc:
        logger.error("exec timeout=%s", timeout, extra={"command": command_text}, exc_info=True)
        raise EngineExecError(
            f"{friendly_name} 执行超时（{timeout} 秒）。可尝试减小盒子尺寸或降低 exhaustiveness。",
            command=full_command,
            stdout=exc.stdout if isinstance(exc.stdout, str) else "",
            stderr=exc.stderr if isinstance(exc.stderr, str) else "",
        ) from exc
    except OSError as exc:
        logger.error("exec os_error=%s", exc, extra={"command": command_text}, exc_info=True)
        raise EngineExecError(
            f"{friendly_name} 启动失败：{exc}",
            command=full_command,
        ) from exc

    result = ProcessResult(
        command=full_command,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        duration_seconds=round(time.monotonic() - started, 3),
        ok=proc.returncode == 0,
    )

    if not result.ok:
        detail = _friendly_stderr(result.stderr)
        logger.error(
            "exec failed returncode=%s stderr=%s",
            result.returncode,
            result.stderr[-2000:],
            extra={"command": command_text},
        )
        raise EngineExecError(
            f"{friendly_name} 运行失败（退出码 {result.returncode}）。{detail}",
            command=full_command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return result


def run_command_detached(command: list[str]) -> int:
    """以非阻塞方式启动外部程序（如打开 PyMOL），返回进程 PID。"""

    executable = resolve_executable(command[0])
    full_command = [executable, *command[1:]]
    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(full_command, **kwargs)
    return proc.pid


def _friendly_stderr(stderr: str) -> str:
    """从原始 stderr 中提取关键信息，生成友好提示。"""

    stderr = (stderr or "").strip()
    if not stderr:
        return "请检查输入结构、对接盒子参数与可执行程序是否正常。"
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    head = lines[0] if lines else ""
    keywords = {
        "not found": "输入文件不存在或路径错误",
        "unable to open": "无法打开输入文件，请检查文件是否完整",
        "toast": "配体可旋转键处理失败，请检查分子结构",
        "out of memory": "内存不足，请减小盒子尺寸或减少并行任务",
        "permission": "权限不足，请检查程序执行权限",
    }
    lowered = stderr.lower()
    for keyword, friendly in keywords.items():
        if keyword in lowered:
            return friendly
    return head[:300]
