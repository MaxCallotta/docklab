"""MOE 引擎适配器模板（预留）。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import EngineNotImplementedError, EngineParamError
from app.models.docking import DockParams, DockResult

from ..base import BaseDockEngine
from ..registry import register_engine


@register_engine
class MoeEngine(BaseDockEngine):
    """MOE Docking 适配器（预留）。"""

    engine_id = "moe"
    engine_name = "MOE"
    description = "MOE Dock 对接（预留模板）"

    def set_params(self, params: DockParams) -> None:
        if params.engine_id != self.engine_id:
            raise EngineParamError("参数引擎与当前引擎不一致")
        self.params = params

    def preprocess_receptor(self, receptor_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("MOE 受体准备将在适配器落地时实现。")

    def preprocess_ligand(self, ligand_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("MOE 配体准备将在适配器落地时实现。")

    def run_dock(self, receptor_pdbqt: Path, ligand_pdbqt: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("MOE 执行逻辑为预留模板，尚未实现。")

    def parse_result(self, output_path: Path, log_path: Path | None = None) -> DockResult:
        raise EngineNotImplementedError("MOE 结果解析为预留模板，尚未实现。")
