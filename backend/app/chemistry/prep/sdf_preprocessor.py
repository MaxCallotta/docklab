"""SDF 配体预处理：RDKit 校验 -> 3D/加氢 -> PDBQT。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeValidationError
from app.models.molecule import ParsedMolecule, PreparedLigand, PreprocessResult
from app.utils.file_utils import ensure_dir

from ..converters.openbabel_converter import OpenBabelConverter
from ..converters.rdkit_converter import RdkItConverter, rdkit_available
from ..parsers.sdf_parser import SdfParser
from .base import BasePreprocessor
from .registry import register_preprocessor


def prepare_sdf_ligands(
    parsed: ParsedMolecule,
    prepared_dir: Path,
    *,
    input_type: str,
    source_path: Path | None = None,
) -> PreprocessResult:
    """将已解析的 SDF 分子文件归一化并生成 PDBQT，供 SDF/mol/mol2 预处理复用。"""

    ligands: list[PreparedLigand] = []
    skipped: list[str] = []
    for index, mol_file in enumerate(parsed.mol_files, start=1):
        normalized_sdf = prepared_dir / f"ligand_{index:03d}_ready.sdf"
        try:
            if rdkit_available():
                # 校验 + 加氢 + 3D 构象（若缺失）
                from rdkit import Chem  # noqa: PLC0415

                supplier = Chem.SDMolSupplier(str(mol_file), sanitize=True, removeHs=False)
                mol = next((m for m in supplier if m is not None), None)
                if mol is None:
                    raise MoleculeValidationError(f"SDF 中未找到有效分子：{mol_file}")
                writer = Chem.SDWriter(str(normalized_sdf))
                writer.write(mol)
                writer.close()
            else:
                normalized_sdf = mol_file

            pdbqt_path = prepared_dir / f"ligand_{index:03d}.pdbqt"
            OpenBabelConverter.to_pdbqt_ligand(normalized_sdf, pdbqt_path)
        except Exception as exc:
            skipped.append(f"分子 {index} 预处理失败，已跳过：{exc}")
            continue

        properties: dict = {}
        warnings: list[str] = []
        if rdkit_available():
            try:
                properties = RdkItConverter.compute_properties(normalized_sdf)
            except Exception as exc:
                warnings.append(f"分子 {index} 属性计算失败：{exc}")

        ligands.append(
            PreparedLigand(
                index=index,
                name=mol_file.stem,
                sdf_path=normalized_sdf,
                pdbqt_path=pdbqt_path,
                properties=properties,
                warnings=warnings,
            )
        )

    if not ligands:
        raise MoleculeValidationError(
            "文件中未找到可生成 PDBQT 的有效分子，请检查结构是否完整（如断键、孤立原子）。"
        )
    if len(ligands) == 1:
        ligands[0].smiles = parsed.smiles

    return PreprocessResult(
        input_type=input_type,
        role="ligand",
        source_path=source_path or parsed.source_path,
        num_molecules=len(ligands),
        ligands=ligands,
        warnings=parsed.warnings + skipped,
    )


@register_preprocessor
class SdfPreprocessor(BasePreprocessor):
    """SDF 配体预处理。"""

    input_type = "sdf"
    role = "ligand"

    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        """执行 SDF 配体预处理。"""

        parsed = SdfParser().parse(source)
        prepared_dir = ensure_dir(work_dir / "prepared")
        return prepare_sdf_ligands(
            parsed,
            prepared_dir,
            input_type=self.input_type,
            source_path=source,
        )
