"""分子解析器抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.core.exceptions import FileNotFoundAppError, FormatUnsupportedError
from app.models.molecule import ParsedMolecule


class BaseMoleculeParser(ABC):
    """统一分子解析接口。

    新增分子格式时，只需实现本类的 parse() 并注册到 PARSER_REGISTRY，
    业务调度代码无需任何修改（开闭原则）。
    """

    format_name: str = ""
    extensions: tuple[str, ...] = ()

    def validate(self, path: Path) -> None:
        """基础校验：文件存在 + 后缀匹配。"""

        if not path.exists():
            raise FileNotFoundAppError(f"分子文件不存在：{path}")
        if path.suffix.lower() not in self.extensions:
            raise FormatUnsupportedError(
                f"格式 {path.suffix} 不属于 {self.format_name} 解析器"
            )

    @abstractmethod
    def parse(self, path: Path) -> ParsedMolecule:
        """解析分子文件，返回标准化 ParsedMolecule。"""
