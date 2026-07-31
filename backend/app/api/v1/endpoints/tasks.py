"""任务管理端点：CRUD / 重启 / 删除 / 打包下载。"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.core.constants import TaskDirName, TaskStatus
from app.core.exceptions import RequestParamError
from app.core.response import ok
from app.services.pose_service import PoseService
from app.services.task_manager import TaskManager

from ..deps import get_task_manager
from ..schemas.task import BatchDeleteRequest, CreateTaskRequest, ExportPoseRequest


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("")
def create_task(
    request: CreateTaskRequest,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """创建任务。"""

    record = manager.create_task(
        request.name,
        engine_id=request.engine_id,
        params=request.params,
        input_files=request.input_files,
    )
    return ok(record.to_dict(), "任务创建成功")


@router.get("")
def list_tasks(
    status: str | None = None,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """查询任务历史，可按状态过滤。"""

    if status and status not in (
        TaskStatus.QUEUED,
        TaskStatus.RUNNING,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
    ):
        raise HTTPException(status_code=400, detail=f"非法状态：{status}")
    records = manager.list_tasks(status=status)
    return ok({"tasks": [record.to_dict() for record in records]}, "任务列表获取成功")


@router.get("/{task_id}")
def get_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """查询单个任务。"""

    return ok(manager.get_task(task_id).to_dict(), "任务详情获取成功")


@router.post("/{task_id}/restart")
def restart_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """重启失败任务。"""

    return ok(manager.restart_task(task_id).to_dict(), "任务已重新排队")


@router.delete("/{task_id}")
def delete_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """删除单个任务。"""

    manager.delete_task(task_id)
    return ok({"deleted": task_id}, "任务已删除")


@router.post("/batch-delete")
def batch_delete(
    request: BatchDeleteRequest,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """批量删除任务。"""

    deleted = manager.delete_tasks(request.task_ids)
    return ok({"deleted_count": deleted}, "批量删除完成")


@router.get("/{task_id}/download")
def download_task(
    task_id: str,
    manager: TaskManager = Depends(get_task_manager),
) -> FileResponse:
    """打包下载任务全部结果。"""

    zip_path = manager.export_task(task_id)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{task_id}.zip",
    )


@router.get("/{task_id}/files/{kind}/{filename}")
def task_file(
    task_id: str,
    kind: str,
    filename: str,
    manager: TaskManager = Depends(get_task_manager),
) -> FileResponse:
    """安全访问任务目录内的文件（input/prepared/work/output/export）。"""

    if kind not in (
        TaskDirName.INPUT,
        TaskDirName.PREPARED,
        TaskDirName.WORK,
        TaskDirName.OUTPUT,
        TaskDirName.EXPORT,
    ):
        raise RequestParamError(f"非法文件目录：{kind}")
    task_dir = manager.task_dir(task_id).resolve()
    file_path = (task_dir / kind / filename).resolve()
    if not file_path.is_relative_to(task_dir) or not file_path.exists():
        raise RequestParamError(f"文件不存在或越界：{filename}")
    return FileResponse(file_path)


@router.get("/{task_id}/pose/{pose_index}")
def pose_file(
    task_id: str,
    pose_index: int,
    manager: TaskManager = Depends(get_task_manager),
) -> FileResponse:
    """返回指定构象的 PDBQT 文本，供 3Dmol 按构象渲染。"""

    task = manager.get_task(task_id)
    docked = task.output_files.get("docked_pdbqt")
    if not docked or not Path(docked).exists():
        raise HTTPException(status_code=404, detail="任务尚无对接输出文件")
    pose_dir = manager.task_dir(task_id) / TaskDirName.OUTPUT / "poses"
    pose_path = PoseService.extract_pose(Path(docked), pose_index, pose_dir)
    return FileResponse(pose_path, media_type="text/plain")


@router.post("/{task_id}/export-pose")
def export_pose(
    task_id: str,
    request: ExportPoseRequest,
    manager: TaskManager = Depends(get_task_manager),
) -> dict:
    """导出指定构象（pdbqt/pdb/sdf/mol2），返回可下载 URL。"""

    task = manager.get_task(task_id)
    docked = task.output_files.get("docked_pdbqt")
    if not docked or not Path(docked).exists():
        raise HTTPException(status_code=404, detail="任务尚无对接输出文件")

    task_dir = manager.task_dir(task_id)
    export_dir = task_dir / TaskDirName.EXPORT
    pose_pdbqt = PoseService.extract_pose(Path(docked), request.pose_index, export_dir)
    if request.format != "pdbqt":
        pose_pdbqt = PoseService.convert_pose(pose_pdbqt, request.format, export_dir)

    return ok({
        "file_url": f"/api/v1/tasks/{task_id}/files/export/{pose_pdbqt.name}",
        "path": str(pose_pdbqt),
        "format": request.format,
    }, "构象导出成功")
