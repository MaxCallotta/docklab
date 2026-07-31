"""单进程启动器：FastAPI 后端 + 前端静态资源。

用法：
    python scripts/run_app.py --host 127.0.0.1 --port 8000

要求：已执行 scripts/install_deps.py（含前端构建），
或前端 dist 目录已存在。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    """启动统一服务。"""

    parser = argparse.ArgumentParser(description="CADD 平台单进程启动器")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn  # noqa: PLC0415

    from app.core.config import get_settings  # noqa: PLC0415
    from app.main import app  # noqa: PLC0415

    print(f"CADD 平台启动：http://{args.host}:{args.port}")
    print(f"数据目录：{get_settings().pax_data_root}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
