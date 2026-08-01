"""分子预处理工具箱独立 REST 接口。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import FileSizeExceededError
from app.core.response import ok
from app.preprocess.manager import PreprocessManager


router = APIRouter(tags=["preprocess"])


def get_manager() -> PreprocessManager:
    """提供 PreprocessManager 实例。"""

    return PreprocessManager()


class PreprocessOptions(BaseModel):
    """单批次分子处理选项。"""

    add_hydrogens: bool = False
    compute_gasteiger: bool = False
    remove_salts: bool = False
    remove_duplicates: bool = False
    enable_conformations: bool = False
    num_conformations: int = Field(1, ge=1, le=200)
    compute_properties: bool = True
    ph: float = Field(7.4, ge=0, le=14)


class PreprocessRunRequest(BaseModel):
    """提交预处理批次请求。"""

    session_id: str
    file_ids: list[str]
    options: PreprocessOptions = Field(default_factory=PreprocessOptions)
    output_format: str = "sdf"


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    session_id: str | None = Form(default=None),
    manager: PreprocessManager = Depends(get_manager),
) -> dict[str, Any]:
    """批量上传分子文件，返回会话标识与文件记录。"""

    settings = get_settings()
    if not session_id:
        session_id = manager.create_session()
    records = []
    for upload_file in files:
        data = await upload_file.read()
        if len(data) > settings.upload_max_mb * 1024 * 1024:
            raise FileSizeExceededError(f"文件大小超过 {settings.upload_max_mb} MB 限制")
        records.append(manager.add_file(session_id, upload_file.filename or "", data))
    return ok({"session_id": session_id, "files": records}, "文件上传成功")


@router.post("/run")
def run_preprocess(
    request: PreprocessRunRequest,
    manager: PreprocessManager = Depends(get_manager),
) -> dict[str, Any]:
    """提交预处理批次并立即返回 batch_id。"""

    batch_id = manager.submit_batch(
        request.session_id,
        request.file_ids,
        request.options.model_dump(),
        request.output_format,
    )
    return ok({"batch_id": batch_id}, "预处理任务已提交")


@router.get("/status/{batch_id}")
def batch_status(
    batch_id: str,
    manager: PreprocessManager = Depends(get_manager),
) -> dict[str, Any]:
    """查询批次处理进度与各分子状态。"""

    return ok(manager.status(batch_id), "预处理状态获取成功")


@router.get("/download/{file_id}")
def download_file(
    file_id: str,
    manager: PreprocessManager = Depends(get_manager),
) -> FileResponse:
    """下载单个处理后文件；未处理时回退到源文件。"""

    path = manager.resolve_download(file_id)
    return FileResponse(path, filename=path.name)


@router.get("/download/batch/{batch_id}")
def download_batch(
    batch_id: str,
    manager: PreprocessManager = Depends(get_manager),
) -> FileResponse:
    """批量打包下载整个预处理批次。"""

    zip_path = manager.make_batch_zip(batch_id)
    return FileResponse(zip_path, media_type="application/zip", filename=f"{batch_id}.zip")


@router.get("/download/{file_id}/{filename}")
def download_file_named(
    file_id: str,
    filename: str,
    manager: PreprocessManager = Depends(get_manager),
) -> FileResponse:
    """带文件名下载单个处理后文件，便于前端 3D 预览识别格式。"""

    path = manager.resolve_download(file_id)
    return FileResponse(path, filename=filename)
