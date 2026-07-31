"""分子解析器注册表。"""

from __future__ import annotations

from pathlib import Path

from app.core.constants import ALLOWED_UPLOAD_EXTENSIONS
from app.core.exceptions import FormatUnsupportedError

from .base import BaseMoleculeParser


PARSER_REGISTRY: dict[str, type[BaseMoleculeParser]] = {}

# EXTENSION-POINT：新增分子输入格式时，在 chemistry/parsers/ 下新建解析器子类并加 @register_parser。


def register_parser(cls: type[BaseMoleculeParser]) -> type[BaseMoleculeParser]:
    """类装饰器：将解析器注册进注册表。"""

    PARSER_REGISTRY[cls.format_name] = cls
    return cls


def get_parser(format_name: str) -> type[BaseMoleculeParser]:
    """按格式名获取解析器类。"""

    parser_cls = PARSER_REGISTRY.get(format_name)
    if parser_cls is None:
        raise FormatUnsupportedError(
            f"未注册的分子格式：{format_name}。已支持：{', '.join(sorted(PARSER_REGISTRY))}"
        )
    return parser_cls


def list_parser_names() -> list[str]:
    """返回全部已注册格式名。"""

    return sorted(PARSER_REGISTRY)


def detect_format(path: Path | str) -> str:
    """根据文件后缀推断格式标识。"""

    suffix = Path(path).suffix.lower()
    format_name = ALLOWED_UPLOAD_EXTENSIONS.get(suffix)
    if format_name is None:
        raise FormatUnsupportedError(f"不支持的文件后缀：{suffix}")
    return format_name
