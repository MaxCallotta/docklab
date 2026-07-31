"""本地 PyMOL 程序探测与唤起。"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.exceptions import PymolNotFoundError
from app.utils.subprocess_runner import run_command_detached


class PymolLauncher:
    """封装 PyMOL 可执行程序发现与本地打开。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._pymol_bin = self.find_pymol()

    def find_pymol(self) -> str:
        """按优先级探测 PyMOL：环境变量 -> PATH -> Windows 常见安装目录。"""

        candidates = [self.settings.pymol_bin]
        if os.name == "nt":
            candidates += [
                r"C:\Program Files\PyMOL\pymol.exe",
                r"C:\Program Files (x86)\PyMOL\pymol.exe",
            ]
        candidates.append(shutil.which("pymol"))

        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate)
            if path.exists():
                return str(path)
        raise PymolNotFoundError(
            "未找到本地 PyMOL。请安装 PyMOL 并配置 PYMOL_BIN 环境变量。"
        )

    def open_local_pymol(self, pml_path: Path | str) -> int:
        """一键唤起本地 PyMOL 打开 PML 脚本，返回进程 PID。"""

        pml_path = Path(pml_path)
        if not pml_path.exists():
            raise PymolNotFoundError(f"PML 脚本不存在：{pml_path}")
        return run_command_detached([self._pymol_bin, str(pml_path)])
