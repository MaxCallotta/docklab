"""CDXML 解析器（基于 OpenBabel）。

行为约定：
- cdxml -> SDF（自动补氢、生成 3D）；
- 多分子 cdxml 自动拆分为独立 SDF 文件，供批量任务使用；
- 破损 cdxml / 空分子抛出统一 MoleculeParseError。
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeParseError
from app.models.molecule import ParsedMolecule
from app.utils.file_utils import ensure_dir, iter_sdf_records, split_sdf_records

from ..converters.openbabel_converter import OpenBabelConverter
from ..converters.rdkit_converter import RdkItConverter, rdkit_available
from .cdxml_normalizer import normalize_cdxml
from .base import BaseMoleculeParser
from .registry import register_parser


@register_parser
class CdxmlParser(BaseMoleculeParser):
    """ChemDraw XML 格式解析器。"""

    format_name = "cdxml"
    extensions = (".cdxml",)

    def parse(self, path: Path) -> ParsedMolecule:
        """解析 cdxml 并返回标准化结果。"""

        self.validate(path)
        work_dir = ensure_dir(path.parent / f"{path.stem}_cdxml_work")
        output_sdf = work_dir / f"{path.stem}.sdf"

        try:
            normalized_cdxml, normalized = normalize_cdxml(
                path,
                work_dir / f"{path.stem}_normalized.cdxml",
            )
            OpenBabelConverter.to_sdf(normalized_cdxml, output_sdf, add_h=True, gen3d=True)
        except Exception as exc:
            if isinstance(exc, MoleculeParseError):
                raise
            raise MoleculeParseError(
                f"cdxml 解析失败：{exc}。请检查文件是否为有效的 ChemDraw XML 且包含分子结构。"
            ) from exc

        records = list(iter_sdf_records(output_sdf))
        if not records:
            raise MoleculeParseError("cdxml 中未解析出任何分子，请检查文件内容。")

        # 多分子自动拆分：每个分子生成独立 SDF 文件
        if len(records) == 1:
            mol_files = [output_sdf]
        else:
            mol_files = split_sdf_records(output_sdf, work_dir / "split", prefix="ligand")

        smiles = ""
        warnings: list[str] = []
        if normalized:
            warnings.append("检测到 ChemDraw 片段标签，已自动合并为完整分子。")
        if rdkit_available():
            try:
                smiles = RdkItConverter.sdf_to_smiles(mol_files[0])
            except Exception:
                warnings.append("RDKit 属性计算失败，仅保留 OpenBabel 转换结果。")

        if len(mol_files) > 1:
            warnings.append(f"检测到 {len(mol_files)} 个分子，已自动拆分为批量配体。")

        return ParsedMolecule(
            format_name=self.format_name,
            source_path=path,
            num_molecules=len(mol_files),
            mol_files=mol_files,
            smiles=smiles,
            warnings=warnings,
        )
