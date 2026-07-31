"""预处理注册表。"""

from __future__ import annotations

from app.core.exceptions import FormatUnsupportedError

from .base import BasePreprocessor


PREPROCESSOR_REGISTRY: dict[str, type[BasePreprocessor]] = {}

# EXTENSION-POINT：新增分子格式预处理时，在 chemistry/prep/ 下新建子类并加 @register_preprocessor，
# 输入类型自动路由，核心调度逻辑零修改。


def register_preprocessor(cls: type[BasePreprocessor]) -> type[BasePreprocessor]:
    """类装饰器：注册预处理子类。"""

    PREPROCESSOR_REGISTRY[cls.key()] = cls
    return cls


def get_preprocessor(input_type: str, role: str) -> type[BasePreprocessor]:
    """按 input_type + role 获取预处理类。"""

    key = f"{role}:{input_type}"
    cls = PREPROCESSOR_REGISTRY.get(key)
    if cls is None:
        raise FormatUnsupportedError(
            f"未注册的预处理类型：{key}。已支持：{', '.join(sorted(PREPROCESSOR_REGISTRY))}"
        )
    return cls


def list_preprocessors() -> list[str]:
    """返回全部已注册预处理类型。"""

    return sorted(PREPROCESSOR_REGISTRY)
