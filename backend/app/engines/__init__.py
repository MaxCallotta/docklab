"""对接引擎调度层（核心可扩展模块）。

显式导入全部引擎子类，确保 @register_engine 装饰器在进程启动时执行，
注册表在任何业务代码调用前即可包含全部引擎。
"""

from . import autodock4, vina
from .extensions import glide, ledock, moe, rdock
from .registry import ENGINE_REGISTRY, get_engine, list_engines, register_engine

__all__ = [
    "ENGINE_REGISTRY",
    "get_engine",
    "list_engines",
    "register_engine",
]
