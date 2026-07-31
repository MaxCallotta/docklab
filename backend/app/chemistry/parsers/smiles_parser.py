"""SMILES 字符串解析器（.txt/.smi 每行一个分子）。"""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import MoleculeValidationError
from app.models.molecule import ParsedMolecule
from app.utils.file_utils import ensure_dir

from .base import BaseMoleculeParser
from .registry import register_parser


@register_parser
class SmilesParser(BaseMoleculeParser):
    """SMILES 文本解析器。"""

    format_name = "smiles"
    extensions = (".txt", ".smi")

    def parse(self, path: Path) -> ParsedMolecule:
        """读取 SMILES 行，逐行生成独立 .smi 文件供批量处理。"""

        self.validate(path)
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        smiles_lines = [
            line.strip()
            for line in raw_lines
            if line.strip() and not line.strip().startswith("#")
        ]
        if not smiles_lines:
            raise MoleculeValidationError("SMILES 文件为空或不包含任何分子。")

        work = ensure_dir(path.parent / f"{path.stem}_smiles_work" / "split")
        mol_files: list[Path] = []
        for index, line in enumerate(smiles_lines, start=1):
            smiles = line.split()[0]
            smi_file = work / f"smiles_{index:03d}.smi"
            smi_file.write_text(smiles, encoding="utf-8")
            mol_files.append(smi_file)

        return ParsedMolecule(
            format_name=self.format_name,
            source_path=path,
            num_molecules=len(mol_files),
            mol_files=mol_files,
            smiles=smiles_lines[0].split()[0],
            warnings=[] if len(mol_files) == 1 else [f"检测到 {len(mol_files)} 条 SMILES，已拆分为批量配体。"],
        )
