"""分子解析与预处理结果 DTO。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedMolecule:
    """分子解析结果。"""

    format_name: str
    source_path: Path
    num_molecules: int
    mol_files: list[Path] = field(default_factory=list)
    smiles: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class PreparedLigand:
    """单个配体预处理结果。"""

    index: int
    name: str
    sdf_path: Path | None = None
    pdbqt_path: Path | None = None
    smiles: str = ""
    properties: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class PreparedReceptor:
    """受体预处理结果。"""

    clean_pdb_path: Path
    pdbqt_path: Path
    atom_count_before: int = 0
    atom_count_after: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class PreprocessResult:
    """统一预处理结果：配体可为多个（批量拆分），受体恒为单个。"""

    input_type: str
    role: str
    source_path: Path
    num_molecules: int
    ligands: list[PreparedLigand] = field(default_factory=list)
    receptor: PreparedReceptor | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def primary_path(self) -> Path | None:
        """返回主输出文件（配体取第一个 PDBQT，受体取 PDBQT）。"""

        if self.role == "ligand" and self.ligands:
            return self.ligands[0].pdbqt_path
        if self.receptor is not None:
            return self.receptor.pdbqt_path
        return None
