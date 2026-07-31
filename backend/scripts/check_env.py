"""环境自检脚本：检查 Python 依赖、外部程序与数据目录。"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


MODULES = ["fastapi", "pydantic", "celery", "rdkit", "Bio", "filelock", "httpx"]
EXECUTABLES = ["obabel", "vina", "autodock4", "autogrid4", "pymol"]


def main() -> int:
    """打印环境概览。"""

    from app.core.paths import get_paths

    print("=" * 60)
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"数据根目录: {get_paths().root}")
    print("-" * 60)

    print("Python 依赖:")
    for module in MODULES:
        ok = importlib.util.find_spec(module) is not None
        print(f"  {module:<12} {'OK' if ok else 'MISSING'}")

    print("外部可执行程序:")
    for exe in EXECUTABLES:
        found = shutil.which(exe)
        print(f"  {exe:<12} {found or 'MISSING'}")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
