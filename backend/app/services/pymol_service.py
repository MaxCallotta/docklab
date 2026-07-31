"""PyMOL 服务：为任务生成 PML 并支持本地唤起。"""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.exceptions import FileNotFoundAppError
from app.models.task import TaskRecord
from app.utils.file_utils import ensure_dir

from ..visualization.pml_generator import PmlGenerator
from ..visualization.pymol_launcher import PymolLauncher
from .task_manager import TaskManager


class PymolService:
    """生成标准化 PML 脚本并打开本地 PyMOL。"""

    def __init__(
        self,
        task_manager: TaskManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.task_manager = task_manager or TaskManager(settings=self.settings)
        self.generator = PmlGenerator()
        self._launcher: PymolLauncher | None = None

    def generate_pml_for_task(
        self,
        task: TaskRecord,
        affinity: float | None = None,
    ) -> Path:
        """基于任务结果生成 PML 脚本。"""

        task_dir = self.task_manager.task_dir(task.task_id)
        receptor = task.output_files.get("receptor_pdbqt") or task.input_files.get("receptor")
        ligand = task.output_files.get("docked_pdbqt") or task.input_files.get("ligand")
        if not receptor or not ligand or not Path(receptor).exists() or not Path(ligand).exists():
            raise FileNotFoundAppError("任务缺少受体或配体文件，无法生成 PML。")

        output_dir = ensure_dir(task_dir / "output")
        pml_path = self.generator.export_pml(
            receptor_path=receptor,
            ligand_path=ligand,
            output_path=output_dir / "visualization.pml",
            affinity=affinity,
        )
        self.task_manager.update_status(
            task.task_id,
            task.status,
            output_files={"pml": str(pml_path)},
        )
        return pml_path

    def open_in_pymol(self, task: TaskRecord) -> int:
        """调用本地 PyMOL 打开任务 PML 脚本。"""

        task_dir = self.task_manager.task_dir(task.task_id)
        pml_path = task_dir / "output" / "visualization.pml"
        if not pml_path.exists():
            pml_path = self.generate_pml_for_task(task)
        if self._launcher is None:
            self._launcher = PymolLauncher(settings=self.settings)
        return self._launcher.open_local_pymol(pml_path)
