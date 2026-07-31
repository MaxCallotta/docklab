"""Glide 引擎适配器模板。

接入方式：填充 run_dock / parse_result 中的软件调用与结果解析，
并在业务层注册后即可使用，无需修改调度代码。
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import EngineNotImplementedError, EngineParamError
from app.models.docking import DockParams, DockResult

from ..base import BaseDockEngine
from ..registry import register_engine


@register_engine
class GlideEngine(BaseDockEngine):
    """Schrodinger Glide 适配器（预留）。"""

    engine_id = "glide"
    engine_name = "Glide"
    description = "Schrodinger Glide 对接（预留模板）"

    def set_params(self, params: DockParams) -> None:
        if params.engine_id != self.engine_id:
            raise EngineParamError("参数引擎与当前引擎不一致")
        self.params = params

    def preprocess_receptor(self, receptor_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("Glide 受体准备将在适配器落地时实现（Maestro 格式）。")

    def preprocess_ligand(self, ligand_path: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("Glide 配体准备将在适配器落地时实现。")

    def run_dock(self, receptor_pdbqt: Path, ligand_pdbqt: Path, work_dir: Path) -> Path:
        raise EngineNotImplementedError("Glide 执行逻辑为预留模板，尚未实现。")

    def parse_result(self, output_path: Path, log_path: Path | None = None) -> DockResult:
        raise EngineNotImplementedError("Glide 结果解析为预留模板，尚未实现。")
