"""分子格式解析器（可插拔注册表）。

显式导入全部解析器子类，确保 @register_parser 装饰器在包导入时执行。
"""

from . import cdxml_parser, pdb_parser, pdbqt_parser, sdf_parser, smiles_parser
from .registry import PARSER_REGISTRY, detect_format, get_parser, list_parser_names, register_parser

__all__ = [
    "PARSER_REGISTRY",
    "detect_format",
    "get_parser",
    "list_parser_names",
    "register_parser",
]
