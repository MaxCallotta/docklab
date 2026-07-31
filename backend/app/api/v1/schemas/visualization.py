"""可视化接口请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PmlRequest(BaseModel):
    """生成 PML 请求。"""

    task_id: str = Field(..., description="任务 ID")
    affinity: float | None = Field(None, description="结合能标注（可选）")


class OpenPymolRequest(BaseModel):
    """打开本地 PyMOL 请求。"""

    task_id: str = Field(..., description="任务 ID")
