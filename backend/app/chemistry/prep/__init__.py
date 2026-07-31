"""分子预处理模块（BasePreprocessor 插件体系）。

显式导入全部预处理子类，确保 @register_preprocessor 装饰器在包导入时执行。
"""

from . import (
    cdxml_preprocessor,
    openbabel_ligand_preprocessor,
    pdb_preprocessor,
    sdf_preprocessor,
    smiles_preprocessor,
)
from .registry import (
    PREPROCESSOR_REGISTRY,
    get_preprocessor,
    list_preprocessors,
    register_preprocessor,
)

__all__ = [
    "PREPROCESSOR_REGISTRY",
    "get_preprocessor",
    "list_preprocessors",
    "register_preprocessor",
]
