"""对接引擎注册表。"""

from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import EngineNotFoundError

from .base import BaseDockEngine


ENGINE_REGISTRY: dict[str, type[BaseDockEngine]] = {}

# EXTENSION-POINT：新增对接软件时，在 engines/extensions/ 下新建子类并加 @register_engine，
# 注册表自动发现，业务调度与前端均无需修改。


def register_engine(cls: type[BaseDockEngine]) -> type[BaseDockEngine]:
    """类装饰器：注册引擎子类。"""

    ENGINE_REGISTRY[cls.engine_id] = cls
    return cls


def get_engine(engine_id: str, settings: Settings | None = None) -> BaseDockEngine:
    """按引擎 ID 实例化引擎。"""

    engine_cls = ENGINE_REGISTRY.get(engine_id)
    if engine_cls is None:
        raise EngineNotFoundError(
            f"未注册的对接引擎：{engine_id}。可用引擎：{', '.join(sorted(ENGINE_REGISTRY))}"
        )
    return engine_cls(settings=settings)


def list_engines() -> list[dict]:
    """返回引擎注册信息列表（供前端下拉框）。"""

    return [
        {
            "engine_id": cls.engine_id,
            "engine_name": cls.engine_name,
            "description": cls.description,
            "supported_platforms": list(cls.supported_platforms),
        }
        for cls in ENGINE_REGISTRY.values()
    ]
