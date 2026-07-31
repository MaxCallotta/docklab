"""可视化端点：PML 生成与本地 PyMOL 唤起。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.response import ok
from app.services.pymol_service import PymolService
from app.services.task_manager import TaskManager

from ..deps import get_pymol_service, get_task_manager
from ..schemas.visualization import OpenPymolRequest, PmlRequest


router = APIRouter(prefix="/visualization", tags=["visualization"])


@router.post("/pml")
def generate_pml(
    request: PmlRequest,
    pymol_service: PymolService = Depends(get_pymol_service),
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """生成任务 PML 可视化脚本。"""

    task = manager.get_task(request.task_id)
    pml_path = pymol_service.generate_pml_for_task(task, affinity=request.affinity)
    return ok({"pml_path": str(pml_path)}, "PML 脚本已生成")


@router.post("/pymol/open")
def open_pymol(
    request: OpenPymolRequest,
    pymol_service: PymolService = Depends(get_pymol_service),
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """一键唤起本地 PyMOL 打开 PML 脚本。"""

    task = manager.get_task(request.task_id)
    pid = pymol_service.open_in_pymol(task)
    return ok({"pid": pid}, "已唤起本地 PyMOL")
