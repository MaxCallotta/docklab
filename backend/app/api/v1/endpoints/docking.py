"""对接端点：提交并执行本地对接任务。"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app.chemistry.pocket_predictor import PocketPredictor
from app.core.config import get_settings
from app.models.docking import DockParams
from app.core.response import ok
from app.services.docking_service import DockingService
from app.services.task_manager import TaskManager

from ..deps import get_docking_service, get_task_manager
from ..schemas.docking import AutoPocketRequest, DockRunRequest


router = APIRouter(prefix="/docking", tags=["docking"])


@router.post("/auto-pocket")
def auto_pocket(request: AutoPocketRequest) -> dict:
    """基于受体与配体自动预测最优口袋盒子（FPocket/几何空腔/兜底）。"""

    predictor = PocketPredictor(fpocket_bin=get_settings().fpocket_bin)
    result = predictor.predict(
        request.receptor_path,
        request.ligand_path,
        padding=request.padding,
    )
    return ok(result, "口袋盒子生成成功")


@router.post("/run")
async def run_docking(
    request: DockRunRequest,
    docking_service: DockingService = Depends(get_docking_service),
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """同步执行对接（线程池隔离），返回结果摘要与任务状态。"""

    task = manager.get_task(request.task_id)
    params = DockParams(
        engine_id=request.engine_id,
        receptor_path=Path(request.receptor_path),
        ligand_path=Path(request.ligand_path),
        center_x=request.center_x,
        center_y=request.center_y,
        center_z=request.center_z,
        size_x=request.size_x,
        size_y=request.size_y,
        size_z=request.size_z,
        exhaustiveness=request.exhaustiveness,
        num_modes=request.num_modes,
        energy_range=request.energy_range,
        seed=request.seed,
        cpu=request.cpu,
        timeout_seconds=request.timeout_seconds,
    )
    result = await run_in_threadpool(docking_service.run_docking, task, params)
    updated = manager.get_task(request.task_id)
    return ok({
        "task": updated.to_dict(),
        "result": {
            "engine_id": result.engine_id,
            "num_poses": len(result.poses),
            "best_pose": result.best_pose().to_dict() if result.best_pose() else None,
            "output_pdbqt": str(result.output_path),
            "score_csv": str(result.score_csv) if result.score_csv else "",
        },
    }, "对接计算完成")
