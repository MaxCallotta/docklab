"""分子预处理抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models.molecule import PreprocessResult


class BasePreprocessor(ABC):
    """统一分子预处理接口。

    新增输入格式（如 mol2）时，新增子类并注册即可，
    业务调度层通过 input_type 自动路由，核心逻辑零修改。
    """

    input_type: str = ""
    role: str = ""  # "ligand" 或 "receptor"

    @classmethod
    def key(cls) -> str:
        """注册表主键：role:input_type。"""

        return f"{cls.role}:{cls.input_type}"

    @abstractmethod
    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        """执行完整预处理并返回标准化结果。"""
