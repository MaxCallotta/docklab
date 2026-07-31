"""简易打包分发脚本。

产物：
1. dist/cadd-source-{version}.zip            源码包（二次开发）
2. dist/CaddPlatform/                        便携目录（自带启动脚本）

便携目录首次启动时自动创建 .venv 并安装依赖，后续直接启动。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.8.0"
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules", "dist"}


def _run(cmd: list[str], cwd: Path) -> None:
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(cwd))


def _ignore_common(dirname: str, names: list[str]) -> list[str]:
    """排除构建/缓存/虚拟环境目录。"""

    return [name for name in names if name in IGNORED_DIRS]


def build_frontend() -> None:
    """确保前端生产构建存在。"""

    dist_dir = ROOT / "frontend" / "dist"
    if dist_dir.exists() and any(dist_dir.iterdir()):
        print("前端 dist 已存在，跳过构建")
        return
    _run(["npm", "run", "build"], ROOT / "frontend")


def make_source_zip(out_dir: Path) -> Path:
    """生成源码包。"""

    zip_path = out_dir / f"cadd-source-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in ("backend", "frontend", "configs", "scripts", "docs", "outputs"):
            src = ROOT / folder
            if not src.exists():
                continue
            for file_path in sorted(src.rglob("*")):
                if not file_path.is_file():
                    continue
                if any(part in IGNORED_DIRS for part in file_path.parts):
                    continue
                if file_path.name in {"package-lock.json"}:
                    continue
                zf.write(file_path, file_path.relative_to(ROOT))
        for extra in ("README.md", "README.en.md", "CHANGELOG.md"):
            path = ROOT / extra
            if path.exists():
                zf.write(path, extra)
    return zip_path


def make_portable(out_dir: Path) -> Path:
    """生成便携目录：后端源码 + 前端 dist + 一键启动脚本。"""

    target = out_dir / "CaddPlatform"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    shutil.copytree(ROOT / "backend", target / "backend", ignore=_ignore_common)
    shutil.copytree(ROOT / "frontend" / "dist", target / "frontend" / "dist")
    (target / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts" / "run_app.py", target / "scripts" / "run_app.py")
    shutil.copy2(ROOT / "scripts" / "install_deps.py", target / "scripts" / "install_deps.py")
    shutil.copy2(ROOT / "scripts" / "demo_closed_loop.py", target / "scripts" / "demo_closed_loop.py")
    if (ROOT / "README.md").exists():
        shutil.copy2(ROOT / "README.md", target / "README.md")
    if (ROOT / "README.en.md").exists():
        shutil.copy2(ROOT / "README.en.md", target / "README.en.md")
    if (ROOT / "CHANGELOG.md").exists():
        shutil.copy2(ROOT / "CHANGELOG.md", target / "CHANGELOG.md")
    demo_doc = ROOT / "outputs" / "docs" / "06-demo-closed-loop.md"
    if demo_doc.exists():
        shutil.copy2(demo_doc, target / "DEMO.md")

    (target / "start.bat").write_text(
        "@echo off\n"
        "cd /d %~dp0\n"
        "if not exist .venv (python -m venv .venv)\n"
        "call .venv\\Scripts\\activate.bat\n"
        "python -m pip install -r backend\\requirements.txt\n"
        "python scripts\\run_app.py --host 127.0.0.1 --port 8000\n",
        encoding="utf-8",
    )
    (target / "start.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -e\n"
        "cd \"$(dirname \"$0\")\"\n"
        "if [ ! -d .venv ]; then python3 -m venv .venv; fi\n"
        "source .venv/bin/activate\n"
        "python -m pip install -r backend/requirements.txt\n"
        "python scripts/run_app.py --host 127.0.0.1 --port 8000\n",
        encoding="utf-8",
    )
    return target


def main() -> int:
    """执行打包。"""

    parser = argparse.ArgumentParser(description="CADD 平台打包")
    parser.add_argument("--out", default=str(ROOT / "dist" / "package"))
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_build:
        build_frontend()

    zip_path = make_source_zip(out_dir)
    portable = make_portable(out_dir)
    print(f"\n源码包: {zip_path}")
    print(f"便携目录: {portable}")
    print("便携目录启动：Windows 双击 start.bat；macOS/Linux 执行 ./start.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
