"""PyInstaller 独立程序入口。

构建命令示例（Windows）：
    pip install pyinstaller
    python scripts/build_standalone_windows.py
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parents[1]

BACKEND_DIR = BASE_DIR / "backend"
if BACKEND_DIR.exists():
    sys.path.insert(0, str(BACKEND_DIR))


def _pick_port(preferred: int) -> int:
    """优先使用指定端口，被占用时自动选择空闲端口。"""

    def _available(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
                return True
            except OSError:
                return False

    if _available(preferred):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _open_browser_when_ready(url: str) -> None:
    """服务可访问后自动打开默认浏览器。"""

    for _ in range(80):
        time.sleep(0.5)
        try:
            urllib.request.urlopen(url, timeout=1).close()
            webbrowser.open(url)
            return
        except OSError:
            continue


def main() -> int:
    """启动 Uvicorn 并托管前端静态资源。"""

    import uvicorn  # noqa: PLC0415

    from app.main import app  # noqa: PLC0415

    preferred_port = int(os.environ.get("CADD_PORT", "8000"))
    port = _pick_port(preferred_port)
    url = f"http://127.0.0.1:{port}"
    print(f"CADD 分子对接平台已启动：{url}")
    if os.environ.get("CADD_NO_BROWSER") != "1":
        threading.Thread(
            target=_open_browser_when_ready,
            args=(url,),
            daemon=True,
        ).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
