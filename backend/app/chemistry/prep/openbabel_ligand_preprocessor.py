"""mol / mol2 配体预处理：OpenBabel 转 SDF 后复用 SDF 流水线。"""

from __future__ import annotations

from pathlib import Path

from app.models.molecule import PreprocessResult
from app.utils.file_utils import ensure_dir

from ..converters.openbabel_converter import OpenBabelConverter
from ..parsers.sdf_parser import SdfParser
from .base import BasePreprocessor
from .registry import register_preprocessor
from .sdf_preprocessor import prepare_sdf_ligands


class _ObabelLigandPreprocessor(BasePreprocessor):
    """通过 OpenBabel 将非 SDF 配体格式归一化为 SDF 再继续预处理。"""

    role = "ligand"
    input_type = ""

    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        prepared_dir = ensure_dir(work_dir / "prepared")
        converted_sdf = prepared_dir / f"{source.stem}.sdf"
        OpenBabelConverter.to_sdf(source, converted_sdf, add_h=True, gen3d=True)
        parsed = SdfParser().parse(converted_sdf)
        return prepare_sdf_ligands(
            parsed,
            prepared_dir,
            input_type=self.input_type,
            source_path=source,
        )


@register_preprocessor
class MolPreprocessor(_ObabelLigandPreprocessor):
    """MDL mol 配体预处理。"""

    input_type = "mol"


@register_preprocessor
class Mol2Preprocessor(_ObabelLigandPreprocessor):
    """Tripos mol2 配体预处理。"""

    input_type = "mol2"
