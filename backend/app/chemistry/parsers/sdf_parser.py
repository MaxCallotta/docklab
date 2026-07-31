"""SDF 解析器：RDKit 校验 + 轻量记录拆分。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeParseError
from app.models.molecule import ParsedMolecule
from app.utils.file_utils import iter_sdf_records

from ..converters.rdkit_converter import RdkItConverter, rdkit_available
from .base import BaseMoleculeParser
from .registry import register_parser


@register_parser
class SdfParser(BaseMoleculeParser):
    """SDF 格式解析器。"""

    format_name = "sdf"
    extensions = (".sdf",)

    def parse(self, path: Path) -> ParsedMolecule:
        """解析 SDF，统计分子数并执行 RDKit 合法性校验。"""

        self.validate(path)
        records = list(iter_sdf_records(path))
        if not records:
            raise MoleculeParseError("SDF 文件中未找到任何分子记录。")

        smiles = ""
        warnings: list[str] = []
        if rdkit_available():
            try:
                smiles = RdkItConverter.sdf_to_smiles(path)
            except Exception as exc:
                raise MoleculeParseError(f"SDF 分子合法性校验失败：{exc}") from exc
        else:
            warnings.append("RDKit 未安装，跳过分子合法性校验。")

        return ParsedMolecule(
            format_name=self.format_name,
            source_path=path,
            num_molecules=len(records),
            mol_files=[path] if len(records) == 1 else self._split(path),
            smiles=smiles,
            warnings=warnings,
        )

    @staticmethod
    def _split(path: Path) -> list[Path]:
        """多分子 SDF 拆分。"""

        from app.utils.file_utils import ensure_dir, split_sdf_records  # noqa: PLC0415

        work = ensure_dir(path.parent / f"{path.stem}_sdf_work" / "split")
        return split_sdf_records(path, work, prefix="ligand")
