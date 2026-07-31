"""分子接口请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PrepareReceptorRequest(BaseModel):
    """受体准备请求（PDB ID 方式）。"""

    pdb_id: str = Field(..., min_length=4, max_length=4, description="RCSB PDB ID")


class SmilesRequest(BaseModel):
    """SMILES 配体生成请求。"""

    smiles: str = Field(..., min_length=1, max_length=2000, description="SMILES 字符串")
