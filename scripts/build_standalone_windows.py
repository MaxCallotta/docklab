"""Windows 独立可执行程序构建（可选）。

前置条件：
    pip install pyinstaller
    python scripts/install_deps.py

产物：dist/CaddPlatform/CaddPlatform.exe
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """调用 PyInstaller 构建单文件程序。"""

    if shutil.which("pyinstaller") is None:
        print("未找到 PyInstaller，请先执行：python -m pip install pyinstaller")
        return 1

    dist_dir = ROOT / "frontend" / "dist"
    if not dist_dir.exists():
        print("前端 dist 不存在，请先执行 python scripts/install_deps.py")
        return 1

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        str(ROOT / "scripts" / "cadd_platform.spec"),
    ]
    subprocess.check_call(cmd, cwd=str(ROOT))
    print(f"构建完成：{ROOT / 'dist' / 'CaddPlatform.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
