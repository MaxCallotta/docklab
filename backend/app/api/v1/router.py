"""API v1 路由汇总。"""

from __future__ import annotations

from fastapi import APIRouter

from .endpoints import docking, molecules, system, tasks, visualization


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system.router)
api_router.include_router(tasks.router)
api_router.include_router(molecules.router)
api_router.include_router(docking.router)
api_router.include_router(visualization.router)
