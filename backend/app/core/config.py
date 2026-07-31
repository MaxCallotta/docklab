"""全局配置加载。

配置优先级：
1. 环境变量（最高）
2. 数据目录 config/engines.json 运行期配置
3. 系统 PATH 自动探测

代码中禁止硬编码绝对路径，统一通过本模块获取。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def _default_data_root() -> Path:
    """返回默认数据目录：优先使用环境变量，未指定时使用当前用户平台数据目录。"""

    env_root = os.environ.get("PAX_DATA_ROOT")
    if env_root:
        return Path(env_root)
    local_root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    return local_root / "CaddPlatform" / "data"


DEFAULT_PAX_DATA_ROOT = _default_data_root()


def _bundled_external_dir() -> Path | None:
    """定位 PyInstaller 打包附带的外部计算引擎目录。"""

    if not getattr(sys, "frozen", False):
        return None
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    external_dir = bundle_root / "external"
    return external_dir if external_dir.exists() else None


def _bundled(*relative_parts: str) -> str:
    """返回打包附带工具的真实路径，未打包或文件不存在时返回空字符串。"""

    external_dir = _bundled_external_dir()
    if external_dir is None:
        return ""
    candidate = external_dir.joinpath(*relative_parts)
    return str(candidate) if candidate.exists() else ""


def _first_existing(*candidates: str | None) -> str:
    """返回第一个非空且真实存在的路径，否则返回空字符串。"""

    for candidate in candidates:
        if candidate:
            path = Path(candidate)
            if path.exists():
                return str(path)
    return ""


@dataclass(frozen=True)
class EngineConfig:
    """外部对接软件可执行程序路径。"""

    vina_bin: str = ""
    autodock4_bin: str = ""
    autogrid4_bin: str = ""
    obabel_bin: str = ""


@dataclass(frozen=True)
class Settings:
    """后端运行配置快照。"""

    pax_data_root: Path
    log_level: str = "INFO"
    upload_max_mb: int = 200
    default_timeout_seconds: int = 7200
    engine: EngineConfig = field(default_factory=EngineConfig)
    pymol_bin: str = ""
    fpocket_bin: str = ""

    @classmethod
    def load(cls) -> "Settings":
        """从环境变量与运行期配置构建 Settings。"""

        root = Path(os.environ.get("PAX_DATA_ROOT") or str(DEFAULT_PAX_DATA_ROOT)).resolve()

        # 读取运行期配置覆盖（如用户修改了引擎安装路径）
        runtime_config: dict = {}
        config_file = root / "config" / "engines.json"
        if config_file.exists():
            try:
                runtime_config = json.loads(config_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                runtime_config = {}

        def _env(key: str) -> str:
            return os.environ.get(key, "").strip()

        engine = EngineConfig(
            vina_bin=_first_existing(
                _env("VINA_BIN"),
                _bundled("autodock_vina", "vina.exe"),
                str(runtime_config.get("vina_bin", "")),
                shutil.which("vina"),
            ),
            autodock4_bin=_first_existing(
                _env("AUTODOCK4_BIN"),
                _bundled("autodock_tools", "autodock4.exe"),
                str(runtime_config.get("autodock4_bin", "")),
                shutil.which("autodock4"),
            ),
            autogrid4_bin=_first_existing(
                _env("AUTOGrid4_BIN"),
                _bundled("autodock_tools", "autogrid4.exe"),
                str(runtime_config.get("autogrid4_bin", "")),
                shutil.which("autogrid4"),
            ),
            obabel_bin=_first_existing(
                _env("OBABEL_BIN"),
                _bundled("openbabel", "obabel.exe"),
                str(runtime_config.get("obabel_bin", "")),
                shutil.which("obabel"),
            ),
        )

        pymol_bin = _first_existing(
            _env("PYMOL_BIN"),
            _bundled("pymol", "pymol.exe"),
            str(runtime_config.get("pymol_bin", "")),
            shutil.which("pymol"),
        )

        fpocket_bin = _first_existing(
            _env("FPOCKET_BIN"),
            _bundled("fpocket", "fpocket.exe"),
            str(runtime_config.get("fpocket_bin", "")),
            shutil.which("fpocket"),
        )

        try:
            upload_max_mb = int(_env("UPLOAD_MAX_MB") or runtime_config.get("upload_max_mb", 200))
        except ValueError:
            upload_max_mb = 200

        return cls(
            pax_data_root=root,
            log_level=_env("LOG_LEVEL") or "INFO",
            upload_max_mb=upload_max_mb,
            engine=engine,
            pymol_bin=pymol_bin,
            fpocket_bin=fpocket_bin,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """进程内全局唯一 Settings 实例。"""

    return Settings.load()
