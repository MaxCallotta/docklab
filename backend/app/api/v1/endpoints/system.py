"""系统端点：健康检查、引擎列表、环境信息。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app import __version__
from app.core.config import get_settings
from app.core.logging import iter_log_entries
from app.core.paths import get_paths
from app.core.response import ok
from app.engines.registry import get_engine, list_engines
from app.services.config_service import ConfigService

from ..deps import get_config_service
from ..schemas.system import SaveConfigRequest, SaveTemplateRequest

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
def health() -> dict:
    """健康检查。"""

    return ok({"status": "ok", "version": __version__}, "健康检查通过")


@router.get("/engines")
def engines() -> dict:
    """返回已注册引擎与本地可用性。"""

    items = []
    for meta in list_engines():
        try:
            check = get_engine(meta["engine_id"]).check_environment()
        except Exception:
            check = None
        items.append({
            **meta,
            "available": check.available if check else False,
            "errors": check.errors if check else ["实例化失败"],
            "hints": check.hints if check else [],
        })
    return ok({"engines": items}, "引擎列表获取成功")


@router.get("/environment")
def environment() -> dict:
    """返回本地环境概览（不含任何分子数据）。"""

    settings = get_settings()
    paths = get_paths()
    return ok({
        "pax_data_root": str(paths.root),
        "tasks_dir": str(paths.tasks_dir),
        "log_level": settings.log_level,
        "obabel": settings.engine.obabel_bin,
        "vina": settings.engine.vina_bin,
        "autodock4": settings.engine.autodock4_bin,
        "autogrid4": settings.engine.autogrid4_bin,
        "pymol": settings.pymol_bin,
    }, "环境信息获取成功")


@router.get("/config")
def get_saved_config(
    config_service: ConfigService = Depends(get_config_service),
) -> dict:
    """读取用户保存的软件路径与全局默认值。"""

    return ok(config_service.get_settings(), "配置读取成功")


@router.post("/config")
def save_saved_config(
    request: SaveConfigRequest,
    config_service: ConfigService = Depends(get_config_service),
) -> dict:
    """保存软件路径与全局默认值（重启后端服务后生效）。"""

    data = config_service.save_settings(request.model_dump(exclude_none=True))
    return ok({"saved": True, "config": data}, "配置保存成功")


@router.get("/templates")
def list_templates(
    config_service: ConfigService = Depends(get_config_service),
) -> dict:
    """列出全部参数模板。"""

    return ok({"templates": config_service.list_templates()}, "模板列表获取成功")


@router.post("/templates")
def save_template(
    request: SaveTemplateRequest,
    config_service: ConfigService = Depends(get_config_service),
) -> dict:
    """保存参数模板。"""

    templates = config_service.save_template(request.name, request.params)
    return ok({"saved": True, "templates": templates}, "参数模板保存成功")


@router.delete("/templates/{name}")
def remove_template(
    name: str,
    config_service: ConfigService = Depends(get_config_service),
) -> dict:
    """删除参数模板。"""

    templates = config_service.delete_template(name)
    return ok({"deleted": name, "templates": templates}, "参数模板已删除")


@router.get("/logs")
def get_logs(
    date: str | None = Query(default=None, description="日期 YYYY-MM-DD，默认今天"),
    level: str | None = Query(default=None, pattern="^(INFO|WARNING|ERROR)$"),
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict:
    """读取本地 JSON 行日志，供前端日志查看页展示。"""

    target_date = date or datetime.now().strftime("%Y-%m-%d")
    entries = iter_log_entries(get_paths().logs_dir, date=target_date, level=level, limit=limit)
    return ok({"date": target_date, "entries": entries}, "日志读取成功")
