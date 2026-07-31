"""任务接口请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTaskRequest(BaseModel):
    """创建任务请求。"""

    name: str = Field(..., min_length=1, max_length=128, description="任务名称")
    engine_id: str = Field("", description="对接引擎 ID")
    params: dict = Field(default_factory=dict, description="对接参数")
    input_files: dict = Field(default_factory=dict, description="输入文件映射")


class BatchDeleteRequest(BaseModel):
    """批量删除任务请求。"""

    task_ids: list[str] = Field(..., min_length=1)


class ExportPoseRequest(BaseModel):
    """导出指定构象请求。"""

    pose_index: int = Field(..., ge=1)
    format: str = Field("pdbqt", pattern="^(pdbqt|pdb|sdf|mol2)$")
