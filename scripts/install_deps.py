"""一键安装依赖（Windows/macOS/Linux 通用）。

用法：
    python scripts/install_deps.py            # 后端 + 前端依赖 + 前端构建
    python scripts/install_deps.py --skip-npm # 仅安装 Python 依赖

说明：
- 使用当前 Python 解释器安装 backend/requirements.txt；
- 前端依赖通过 npm 安装并执行生产构建，供单进程部署模式使用。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> None:
    """执行子进程并透传输出。"""

    print(f"\n[CMD] {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(cwd))


def main() -> int:
    """执行依赖安装。"""

    parser = argparse.ArgumentParser(description="CADD 平台依赖一键安装")
    parser.add_argument("--skip-npm", action="store_true", help="跳过前端依赖安装与构建")
    parser.add_argument("--skip-build", action="store_true", help="跳过前端生产构建")
    args = parser.parse_args()

    backend_dir = ROOT / "backend"
    frontend_dir = ROOT / "frontend"

    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"项目根目录: {ROOT}")
    print("=" * 60)

    print("\n[1/3] 安装后端 Python 依赖")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], backend_dir)

    if args.skip_npm:
        print("\n已跳过前端依赖安装（--skip-npm）")
        return 0

    npm = shutil.which("npm")
    if not npm:
        print("\n未找到 npm，请先安装 Node.js 20+ 后重新运行")
        return 1

    print("\n[2/3] 安装前端依赖")
    run([npm, "install"], frontend_dir)

    if not args.skip_build:
        print("\n[3/3] 构建前端生产产物")
        run([npm, "run", "build"], frontend_dir)

    print("\n依赖安装完成。")
    print("开发模式：npm run dev（frontend 目录） + uvicorn app.main:app（backend 目录）")
    print("单进程模式：python scripts/run_app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
