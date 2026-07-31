"""格式转换器抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseConverter(ABC):
    """统一格式转换接口，后续新增转换后端只需实现本类。"""

    @abstractmethod
    def convert(self, source: Path, destination: Path, **options) -> Path:
        """将 source 转换为 destination 指定格式。"""
