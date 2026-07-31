"""运行期数据目录解析。

所有缓存、任务、日志统一落在 PAX_DATA_ROOT（默认平台用户数据目录），
业务模块只允许通过本模块获取路径，禁止自行拼接。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class RuntimePaths:
    """运行期目录结构。"""

    root: Path
    config_dir: Path
    tasks_dir: Path
    cache_dir: Path
    logs_dir: Path
    tmp_dir: Path
    exports_dir: Path
    pdb_cache_dir: Path

    @classmethod
    def from_settings(cls, settings: Settings) -> "RuntimePaths":
        """依据 Settings 计算全部子目录。"""

        root = settings.pax_data_root
        return cls(
            root=root,
            config_dir=root / "config",
            tasks_dir=root / "tasks",
            cache_dir=root / "cache",
            logs_dir=root / "logs",
            tmp_dir=root / "tmp",
            exports_dir=root / "exports",
            pdb_cache_dir=root / "cache" / "pdb",
        )

    def ensure_all(self) -> None:
        """创建全部运行期目录（幂等）。"""

        for path in (
            self.config_dir,
            self.tasks_dir,
            self.cache_dir,
            self.logs_dir,
            self.tmp_dir,
            self.exports_dir,
            self.pdb_cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def task_dir(self, task_id: str) -> Path:
        """返回指定任务目录。"""

        return self.tasks_dir / task_id


@lru_cache(maxsize=1)
def get_paths() -> RuntimePaths:
    """进程内全局唯一 RuntimePaths 实例。"""

    settings = get_settings()
    paths = RuntimePaths.from_settings(settings)
    paths.ensure_all()
    return paths
