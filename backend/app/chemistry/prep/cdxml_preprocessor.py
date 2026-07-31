"""CDXML 配体预处理：解析 -> 拆分 -> PDBQT 转换。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import LigandPrepError
from app.models.molecule import PreparedLigand, PreprocessResult
from app.utils.file_utils import ensure_dir

from ..converters.openbabel_converter import OpenBabelConverter
from ..converters.rdkit_converter import RdkItConverter, rdkit_available
from ..parsers.cdxml_parser import CdxmlParser
from .base import BasePreprocessor
from .registry import register_preprocessor


@register_preprocessor
class CdxmlPreprocessor(BasePreprocessor):
    """cdxml -> SDF -> PDBQT 配体预处理。"""

    input_type = "cdxml"
    role = "ligand"

    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        """执行 cdxml 配体预处理，支持多分子自动拆分。"""

        parsed = CdxmlParser().parse(source)
        prepared_dir = ensure_dir(work_dir / "prepared")
        ligands: list[PreparedLigand] = []
        skipped: list[str] = []

        for index, mol_file in enumerate(parsed.mol_files, start=1):
            pdbqt_path = prepared_dir / f"ligand_{index:03d}.pdbqt"
            try:
                OpenBabelConverter.to_pdbqt_ligand(mol_file, pdbqt_path)
            except Exception as exc:
                skipped.append(f"分子 {index} 无法生成 PDBQT，已跳过：{exc}")
                continue

            properties: dict = {}
            warnings: list[str] = []
            if rdkit_available():
                try:
                    properties = RdkItConverter.compute_properties(mol_file)
                except Exception as exc:
                    warnings.append(f"分子 {index} 属性计算失败：{exc}")

            ligands.append(
                PreparedLigand(
                    index=index,
                    name=mol_file.stem,
                    sdf_path=mol_file,
                    pdbqt_path=pdbqt_path,
                    properties=properties,
                    warnings=warnings,
                )
            )

        if not ligands:
            raise LigandPrepError(
                f"cdxml 中 {len(parsed.mol_files)} 个分子均无法生成 PDBQT，"
                "请检查结构是否完整（如断键、孤立原子）。"
            )
        if len(ligands) == 1:
            ligands[0].smiles = parsed.smiles

        return PreprocessResult(
            input_type=self.input_type,
            role=self.role,
            source_path=source,
            num_molecules=len(ligands),
            ligands=ligands,
            warnings=parsed.warnings + skipped,
        )
