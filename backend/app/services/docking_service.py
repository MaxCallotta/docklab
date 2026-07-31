"""对接调度服务：编排引擎流水线并持久化任务状态。"""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.constants import TaskStatus
from app.core.exceptions import AppError
from app.engines.registry import get_engine
from app.models.docking import DockParams, DockResult
from app.models.task import TaskRecord
from app.utils.file_utils import ensure_dir

from .report_service import ReportService
from .task_manager import TaskManager


logger = logging.getLogger("cadd.docking")


class DockingService:
    """封装「任务状态更新 + 引擎流水线 + 报表生成」。"""

    def __init__(
        self,
        task_manager: TaskManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.task_manager = task_manager or TaskManager(settings=self.settings)

    def run_docking(self, task: TaskRecord, params: DockParams) -> DockResult:
        """同步执行完整对接流水线，失败时自动写入标准化错误。"""

        self.task_manager.update_status(
            task.task_id,
            TaskStatus.RUNNING,
            warnings=["对接计算执行中，请勿关闭本地服务。"],
        )
        self.task_manager.update_params(task.task_id, params.to_dict())
        logger.info(
            "docking_start task_id=%s engine=%s receptor=%s ligand=%s",
            task.task_id,
            params.engine_id,
            params.receptor_path,
            params.ligand_path,
        )

        task_dir = self.task_manager.task_dir(task.task_id)
        work_dir = ensure_dir(task_dir / "work")

        try:
            engine = get_engine(params.engine_id, settings=self.settings)
            # 显式调用引擎抽象接口，同时保留受体/配体 PDBQT 路径供 PML 与导出使用
            engine.set_params(params)
            receptor_pdbqt = engine.preprocess_receptor(params.receptor_path, work_dir)
            ligand_pdbqt = engine.preprocess_ligand(params.ligand_path, work_dir)
            output_path = engine.run_dock(receptor_pdbqt, ligand_pdbqt, work_dir)
            log_path = work_dir / f"{engine.engine_id}_run.log"
            result = engine.parse_result(output_path, log_path)

            output_dir = ensure_dir(task_dir / "output")
            score_csv = ReportService.write_score_csv(result.poses, output_dir / "scores.csv")
            result.score_csv = score_csv

            self.task_manager.update_status(
                task.task_id,
                TaskStatus.COMPLETED,
                result_summary=ReportService.build_result_summary(result),
                output_files={
                    "receptor_pdbqt": str(receptor_pdbqt),
                    "ligand_pdbqt": str(ligand_pdbqt),
                    "docked_pdbqt": str(result.output_path),
                    "score_csv": str(score_csv),
                    "log": str(result.log_path) if result.log_path else "",
                },
                warnings=result.warnings,
            )
            logger.info("docking_complete task_id=%s poses=%s", task.task_id, len(result.poses))
            return result
        except AppError as exc:
            logger.error(
                "docking_failed task_id=%s code=%s msg=%s",
                task.task_id,
                exc.code,
                exc.message,
                exc_info=True,
            )
            self.task_manager.update_status(
                task.task_id,
                TaskStatus.FAILED,
                error_code=exc.code,
                error_message=exc.message,
                warnings=[exc.message],
            )
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("docking_unexpected task_id=%s", task.task_id, exc_info=True)
            self.task_manager.update_status(
                task.task_id,
                TaskStatus.FAILED,
                error_code="INTERNAL_ERROR",
                error_message=f"对接调度异常：{exc}",
            )
            raise AppError(f"对接调度异常：{exc}", code="INTERNAL_ERROR") from exc
