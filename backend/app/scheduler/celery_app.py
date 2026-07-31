"""Celery 实例配置。

使用 Kombu Filesystem Transport 作为本地文件队列：
- 无 Redis / 无数据库；
- 队列消息与结果均落在 D:\\Pax_2.0\\cache\\celery。
"""

from __future__ import annotations

from pathlib import Path

from app.core.paths import get_paths


celery_app = None

try:
    from celery import Celery  # noqa: PLC0415

    paths = get_paths()
    broker_dir = paths.cache_dir / "celery" / "broker"
    backend_dir = paths.cache_dir / "celery" / "backend"
    for sub in ("in", "out", "processed"):
        (broker_dir / sub).mkdir(parents=True, exist_ok=True)
    backend_dir.mkdir(parents=True, exist_ok=True)

    celery_app = Celery("cadd", broker="filesystem://", backend=f"file://{backend_dir.as_posix()}")
    celery_app.conf.update(
        broker_connection_retry_on_startup=True,
        broker_transport_options={
            "data_folder_in": str(broker_dir / "in"),
            "data_folder_out": str(broker_dir / "out"),
            "processed_folder": str(broker_dir / "processed"),
        },
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Shanghai",
        enable_utc=True,
        task_always_eager=False,
    )
except ImportError:
    celery_app = None
