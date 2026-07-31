"""AutoDock 4 引擎适配器（骨架）。

AutoDock 4 需要 AutoGrid 网格图 + DPF 对接参数文件，将在后续阶段实现；
本文件先固定接口签名，保证调度层零修改。
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import EngineNotImplementedError, EngineParamError
from app.models.docking import DockParams, DockResult

from .base import BaseDockEngine
from .registry import register_engine


@register_engine
class AutoDock4Engine(BaseDockEngine):
    """AutoDock 4.2 适配器。"""

    engine_id = "autodock4"
    engine_name = "AutoDock 4"
    description = "AutoDock 4 + AutoGrid 网格对接（预留实现）"

    def _resolve_executable_path(self) -> str:
        return self.settings.engine.autodock4_bin

    def set_params(self, params: DockParams) -> None:
        if params.engine_id != self.engine_id:
            raise EngineParamError(f"参数引擎 {params.engine_id} 与当前引擎 {self.engine_id} 不一致")
        self.params = params

    def preprocess_receptor(self, receptor_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError(
            "AutoDock 4 适配器为预留骨架：受体预处理将复用 PdbPreprocessor，后续阶段补齐。"
        )

    def preprocess_ligand(self, ligand_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError(
            "AutoDock 4 适配器为预留骨架：配体预处理将复用格式 Preprocessor，后续阶段补齐。"
        )

    def run_dock(
        self,
        receptor_pdbqt: Path,
        ligand_pdbqt: Path,
        work_dir: Path,
    ) -> Path:
        raise EngineNotImplementedError(
            "AutoDock 4 执行逻辑（GPF/DPF 生成 + autogrid4/autodock4 调用）将在后续阶段实现。"
        )

    def parse_result(
        self,
        output_path: Path,
        log_path: Path | None = None,
    ) -> DockResult:
        raise EngineNotImplementedError(
            "AutoDock 4 对接结果（DLG/PDBQT）解析将在后续阶段实现。"
        )
