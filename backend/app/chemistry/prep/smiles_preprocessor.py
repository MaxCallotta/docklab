"""SMILES 配体预处理：SMILES -> 3D SDF -> PDBQT。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeValidationError
from app.models.molecule import PreparedLigand, PreprocessResult
from app.utils.file_utils import ensure_dir

from ..converters.openbabel_converter import OpenBabelConverter
from ..converters.rdkit_converter import RdkItConverter, rdkit_available
from .base import BasePreprocessor
from .registry import register_preprocessor


@register_preprocessor
class SmilesPreprocessor(BasePreprocessor):
    """SMILES 字符串配体预处理。"""

    input_type = "smiles"
    role = "ligand"

    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        """逐条 SMILES 生成 3D 构象并转换为 PDBQT。"""

        prepared_dir = ensure_dir(work_dir / "prepared")
        lines = [
            line.strip()
            for line in source.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not lines:
            raise MoleculeValidationError("SMILES 文件为空。")

        ligands: list[PreparedLigand] = []
        for index, line in enumerate(lines, start=1):
            smiles = line.split()[0]
            sdf_path = prepared_dir / f"ligand_{index:03d}.sdf"
            pdbqt_path = prepared_dir / f"ligand_{index:03d}.pdbqt"
            warnings: list[str] = []

            if rdkit_available():
                RdkItConverter.smiles_to_sdf(smiles, sdf_path, add_h=True)
            else:
                OpenBabelConverter.smiles_to_sdf(smiles, sdf_path, gen3d=True)
                warnings.append("RDKit 未安装，SMILES 构象由 OpenBabel 生成。")

            OpenBabelConverter.to_pdbqt_ligand(sdf_path, pdbqt_path)

            properties: dict = {}
            if rdkit_available():
                try:
                    properties = RdkItConverter.compute_properties(sdf_path)
                except Exception as exc:
                    warnings.append(f"分子 {index} 属性计算失败：{exc}")

            ligands.append(
                PreparedLigand(
                    index=index,
                    name=f"smiles_{index:03d}",
                    sdf_path=sdf_path,
                    pdbqt_path=pdbqt_path,
                    smiles=smiles,
                    properties=properties,
                    warnings=warnings,
                )
            )

        return PreprocessResult(
            input_type=self.input_type,
            role=self.role,
            source_path=source,
            num_molecules=len(ligands),
            ligands=ligands,
            warnings=[] if len(ligands) == 1 else [f"检测到 {len(ligands)} 条 SMILES，已拆分为批量配体。"],
        )
