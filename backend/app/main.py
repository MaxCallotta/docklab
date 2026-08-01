"""FastAPI 应用入口。

统一约定：
- 路由前缀 /api/v1；
- 所有业务异常统一转换为 {code, message, data, details} 响应；
- 未捕获异常转换为 INTERNAL_ERROR，避免向前端泄露堆栈。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.preprocess.router import router as preprocess_router
from app.core.constants import ErrorCode
from app.core.exceptions import AppError
from app.core.logging import bind_log_context, reset_log_context, setup_logging
from app.core.paths import get_paths
from app.core.response import fail


logger = setup_logging(log_dir=get_paths().logs_dir)


def _frontend_dist() -> Path:
    """定位前端静态产物目录，兼容源码运行与 PyInstaller 打包。"""

    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        bundled = bundle_root / "frontend" / "dist"
        if bundled.exists():
            return bundled
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


class LogContextMiddleware(BaseHTTPMiddleware):
    """为每个请求绑定操作人与任务 ID 日志上下文。"""

    async def dispatch(self, request: Request, call_next):
        operator = request.headers.get("X-Operator", "local-user")
        match = re.search(r"/tasks/([0-9a-fA-F-]{8,})", request.url.path)
        task_id = match.group(1) if match else ""
        tokens = bind_log_context(operator=operator, task_id=task_id)
        logger.info("request method=%s path=%s", request.method, request.url.path)
        try:
            return await call_next(request)
        finally:
            reset_log_context(tokens)


def create_app() -> FastAPI:
    """构建 FastAPI 应用实例。"""

    app = FastAPI(
        title="CADD 本地分子对接可视化科研平台",
        description="四层架构：前端交互层 / 业务调度服务层 / 分子计算引擎管理层 / 3D 可视化渲染层",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LogContextMiddleware)

    app.include_router(api_router)
    app.include_router(preprocess_router, prefix="/api/preprocess")

    # 单进程部署：后端直接托管前端构建产物（frontend/dist）
    frontend_dist = (
        _frontend_dist()
    )
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """业务异常统一出口。"""

        logger.error("业务异常 code=%s msg=%s", exc.code, exc.message, exc_info=True)
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """兜底异常出口。"""

        import traceback  # noqa: PLC0415

        logger.error("未捕获异常：%s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=fail(
                ErrorCode.INTERNAL_ERROR,
                f"服务器内部错误：{exc}",
                error_detail=traceback.format_exc(),
            ),
        )

    return app


app = create_app()
