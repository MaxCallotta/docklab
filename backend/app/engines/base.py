"""对接引擎抽象基类。

本模块是整个平台最重要的扩展点：
- 所有对接软件（Vina、AutoDock4、Glide、MOE、LeDock、rDock）统一继承 BaseDockEngine；
- 业务调度层只依赖本基类，新增软件时只需新增子类并注册，
  前端与调度逻辑零修改（开闭原则）。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import Settings, get_settings
from app.models.docking import DockParams, DockResult


@dataclass
class EnvironmentCheck:
    """引擎环境检测结果。"""

    engine_id: str
    available: bool
    errors: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)


class BaseDockEngine(ABC):
    """对接引擎统一抽象接口。"""

    engine_id: str = ""
    engine_name: str = ""
    description: str = ""
    supported_platforms: tuple[str, ...] = ("windows", "linux", "darwin")

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.params: DockParams | None = None

    @abstractmethod
    def set_params(self, params: DockParams) -> None:
        """设置对接参数（盒子、exhaustiveness、能量范围等）。"""

    @abstractmethod
    def preprocess_receptor(self, receptor_path: Path, work_dir: Path) -> Path:
        """受体预处理，返回引擎可用的 PDBQT 文件路径。"""

    @abstractmethod
    def preprocess_ligand(self, ligand_path: Path, work_dir: Path) -> Path:
        """配体预处理，返回引擎可用的 PDBQT 文件路径。"""

    @abstractmethod
    def run_dock(
        self,
        receptor_pdbqt: Path,
        ligand_pdbqt: Path,
        work_dir: Path,
    ) -> Path:
        """执行本地对接进程，返回输出构象文件路径。"""

    @abstractmethod
    def parse_result(
        self,
        output_path: Path,
        log_path: Path | None = None,
    ) -> DockResult:
        """解析输出构象与结合自由能打分。"""

    def check_environment(self) -> EnvironmentCheck:
        """检测引擎可执行程序是否可用，返回友好诊断。"""

        executable = self._resolve_executable_path()
        if executable:
            return EnvironmentCheck(engine_id=self.engine_id, available=True)
        return EnvironmentCheck(
            engine_id=self.engine_id,
            available=False,
            errors=[f"{self.engine_name} 可执行程序未找到"],
            hints=[f"请安装 {self.engine_name} 并在数据目录 config/engines.json 中配置路径"],
        )

    def run_pipeline(self, params: DockParams, work_dir: Path) -> DockResult:
        """完整对接流水线：参数 -> 预处理 -> 执行 -> 解析。"""

        self.set_params(params)
        receptor_pdbqt = self.preprocess_receptor(params.receptor_path, work_dir)
        ligand_pdbqt = self.preprocess_ligand(params.ligand_path, work_dir)
        output_path = self.run_dock(receptor_pdbqt, ligand_pdbqt, work_dir)
        log_path = work_dir / f"{self.engine_id}_run.log"
        return self.parse_result(output_path, log_path)

    def _resolve_executable_path(self) -> str:
        """子类可覆盖：返回可执行程序路径。"""

        raise NotImplementedError
