"""对接接口请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DockRunRequest(BaseModel):
    """执行对接请求。"""

    task_id: str = Field(..., description="任务 ID")
    engine_id: str = Field(..., description="引擎 ID，如 vina")
    receptor_path: str = Field(..., description="受体文件绝对路径")
    ligand_path: str = Field(..., description="配体文件绝对路径")
    center_x: float = 0.0
    center_y: float = 0.0
    center_z: float = 0.0
    size_x: float = Field(20.0, gt=0)
    size_y: float = Field(20.0, gt=0)
    size_z: float = Field(20.0, gt=0)
    exhaustiveness: int = Field(8, ge=1)
    num_modes: int = Field(9, ge=1)
    energy_range: float = Field(3.0, gt=0)
    seed: int | None = None
    cpu: int | None = None
    timeout_seconds: int = Field(7200, ge=60)


class AutoPocketRequest(BaseModel):
    """自动口袋盒子预测请求。"""

    receptor_path: str = Field(..., description="受体文件绝对路径（PDB/PDBQT）")
    ligand_path: str | None = Field(None, description="配体文件绝对路径（PDBQT/SDF）")
    padding: float = Field(6.0, ge=0, le=30, description="口袋外扩距离（Å）")
