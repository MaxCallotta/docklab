"""API 依赖注入：进程内单例服务。"""

from __future__ import annotations

from functools import lru_cache

from app.services.config_service import ConfigService
from app.services.docking_service import DockingService
from app.services.molecule_service import MoleculeService
from app.services.pymol_service import PymolService
from app.services.task_manager import TaskManager


@lru_cache(maxsize=1)
def get_task_manager() -> TaskManager:
    """任务管理器单例。"""

    return TaskManager()


@lru_cache(maxsize=1)
def get_molecule_service() -> MoleculeService:
    """分子服务单例。"""

    return MoleculeService()


@lru_cache(maxsize=1)
def get_docking_service() -> DockingService:
    """对接服务单例。"""

    return DockingService(task_manager=get_task_manager())


@lru_cache(maxsize=1)
def get_pymol_service() -> PymolService:
    """PyMOL 服务单例。"""

    return PymolService(task_manager=get_task_manager())


@lru_cache(maxsize=1)
def get_config_service() -> ConfigService:
    """配置服务单例。"""

    return ConfigService()
