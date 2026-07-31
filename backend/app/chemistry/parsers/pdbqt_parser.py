"""PDBQT 解析器（轻量校验，不依赖第三方库）。"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.exceptions import MoleculeParseError
from app.models.molecule import ParsedMolecule

from .base import BaseMoleculeParser
from .registry import register_parser


@register_parser
class PdbqtParser(BaseMoleculeParser):
    """AutoDock PDBQT 格式解析器。"""

    format_name = "pdbqt"
    extensions = (".pdbqt",)

    def parse(self, path: Path) -> ParsedMolecule:
        """校验 PDBQT 原子记录与可旋转键标记。"""

        self.validate(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        atom_lines = [line for line in text.splitlines() if line.startswith(("ATOM", "HETATM"))]
        root_count = len(re.findall(r"^\s*ROOT\s*$", text, flags=re.M))
        branch_count = len(re.findall(r"^\s*BRANCH\s+", text, flags=re.M))
        if not atom_lines:
            raise MoleculeParseError("PDBQT 文件中未找到任何原子记录。")
        return ParsedMolecule(
            format_name=self.format_name,
            source_path=path,
            num_molecules=1,
            mol_files=[path],
            warnings=[f"PDBQT 含 {len(atom_lines)} 个原子、{root_count} 个根片段、{branch_count} 个旋转分支。"],
        )
