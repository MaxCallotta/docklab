"""PDB 解析器。

优先使用 Biopython 统计原子/残基；未安装时降级为轻量行解析，
保证本地环境缺依赖时仍能给出友好错误。
"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeParseError
from app.models.molecule import ParsedMolecule

from .base import BaseMoleculeParser
from .registry import register_parser


@register_parser
class PdbParser(BaseMoleculeParser):
    """标准 PDB 格式解析器。"""

    format_name = "pdb"
    extensions = (".pdb",)

    def parse(self, path: Path) -> ParsedMolecule:
        """校验 PDB 并统计基本结构信息。"""

        self.validate(path)
        try:
            from Bio.PDB import PDBParser  # noqa: PLC0415

            parser = PDBParser(QUIET=True)
            structure = parser.get_structure("receptor", str(path))
            atom_count = sum(1 for _ in structure.get_atoms())
            residue_count = sum(1 for _ in structure.get_residues())
            if atom_count == 0:
                raise MoleculeParseError("PDB 文件中未找到任何原子，请检查文件内容。")
            return ParsedMolecule(
                format_name=self.format_name,
                source_path=path,
                num_molecules=1,
                mol_files=[path],
                warnings=[f"PDB 共 {residue_count} 个残基、{atom_count} 个原子。"],
            )
        except ImportError:
            return self._parse_lightweight(path)
        except MoleculeParseError:
            raise
        except Exception as exc:
            raise MoleculeParseError(f"PDB 解析失败：{exc}") from exc

    @staticmethod
    def _parse_lightweight(path: Path) -> ParsedMolecule:
        """无 Biopython 时的轻量校验。"""

        atom_lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                      if line.startswith(("ATOM", "HETATM"))]
        if not atom_lines:
            raise MoleculeParseError("PDB 文件中未找到 ATOM/HETATM 记录。")
        return ParsedMolecule(
            format_name="pdb",
            source_path=path,
            num_molecules=1,
            mol_files=[path],
            warnings=[f"轻量模式：检测到 {len(atom_lines)} 个原子记录。"],
        )
