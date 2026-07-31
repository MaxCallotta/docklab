"""系统配置接口请求模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SaveConfigRequest(BaseModel):
    """保存软件路径与全局默认值。"""

    engine_paths: dict = Field(default_factory=dict)
    pymol_bin: str = ""
    extra_engines: list[dict] = Field(default_factory=list)
    global_defaults: dict = Field(default_factory=dict)


class SaveTemplateRequest(BaseModel):
    """保存参数模板。"""

    name: str = Field(..., min_length=1, max_length=64)
    params: dict = Field(default_factory=dict)
