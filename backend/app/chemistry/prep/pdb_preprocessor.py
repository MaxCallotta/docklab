"""PDB / PDBQT 受体预处理。

流程：
1. 水分子（HOH/WAT）与杂原子（HETATM）移除；
2. 生成 clean PDB；
3. 转换为 AutoDock PDBQT 受体（优先 AutoDockTools，回退 OpenBabel）。
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

from app.core.exceptions import ReceptorPrepError
from app.models.molecule import PreparedReceptor, PreprocessResult
from app.utils.file_utils import copy_file, ensure_dir, read_text_smart

from ..converters.openbabel_converter import OpenBabelConverter
from .base import BasePreprocessor
from .registry import register_preprocessor


WATER_RESNAMES = {"HOH", "WAT", "H2O"}


@register_preprocessor
class PdbPreprocessor(BasePreprocessor):
    """受体 PDB/PDBQT 预处理。"""

    input_type = "pdb"
    role = "receptor"

    def preprocess(self, source: Path, work_dir: Path) -> PreprocessResult:
        """执行受体预处理。"""

        prepared_dir = ensure_dir(work_dir / "prepared")

        # 已提供 PDBQT：直接使用，跳过结构清理
        if source.suffix.lower() == ".pdbqt":
            pdbqt_path = prepared_dir / f"{source.stem}.pdbqt"
            copy_file(source, pdbqt_path)
            return PreprocessResult(
                input_type=self.input_type,
                role=self.role,
                source_path=source,
                num_molecules=1,
                receptor=PreparedReceptor(
                    clean_pdb_path=source,
                    pdbqt_path=pdbqt_path,
                    warnings=["输入已为 PDBQT，未执行去水/去杂原子。"],
                ),
            )

        clean_pdb = self._clean_pdb(source, prepared_dir)
        pdbqt_path = self._to_pdbqt(clean_pdb, prepared_dir)

        before = self._count_atoms(source)
        after = self._count_atoms(clean_pdb)
        warnings: list[str] = []
        if before - after > 0:
            warnings.append(f"已移除 {before - after} 个水分子/杂原子。")

        return PreprocessResult(
            input_type=self.input_type,
            role=self.role,
            source_path=source,
            num_molecules=1,
            receptor=PreparedReceptor(
                clean_pdb_path=clean_pdb,
                pdbqt_path=pdbqt_path,
                atom_count_before=before,
                atom_count_after=after,
                warnings=warnings,
            ),
        )

    def _clean_pdb(self, source: Path, prepared_dir: Path) -> Path:
        """移除水分子与杂原子，输出 clean PDB。"""

        clean_pdb = prepared_dir / f"{source.stem}_clean.pdb"
        try:
            if importlib.util.find_spec("Bio"):
                self._clean_with_biopython(source, clean_pdb)
            else:
                self._clean_with_lines(source, clean_pdb)
        except Exception as exc:
            raise ReceptorPrepError(f"受体去水/去杂原子失败：{exc}") from exc

        if self._count_atoms(clean_pdb) == 0:
            raise ReceptorPrepError("清理后受体不含任何原子，请检查 PDB 文件。")
        return clean_pdb

    @staticmethod
    def _clean_with_biopython(source: Path, output: Path) -> None:
        """使用 Biopython 按残基级别清理。"""

        from Bio.PDB import PDBIO, PDBParser  # noqa: PLC0415

        structure = PDBParser(QUIET=True).get_structure("rec", str(source))
        for model in structure:
            for chain in model:
                for residue in list(chain):
                    is_water = residue.resname.strip().upper() in WATER_RESNAMES
                    is_hetero = residue.id[0] != " "
                    if is_water or is_hetero:
                        chain.detach_child(residue.id)
        io = PDBIO()
        io.set_structure(structure)
        io.save(str(output))

    @staticmethod
    def _clean_with_lines(source: Path, output: Path) -> None:
        """轻量行级清理（无 Biopython 时使用）。"""

        kept: list[str] = []
        for line in read_text_smart(source).splitlines():
            if not line.startswith("ATOM"):
                continue
            resname = line[17:20].strip().upper()
            if resname in WATER_RESNAMES:
                continue
            kept.append(line)
        output.write_text("\n".join(kept) + "\n", encoding="utf-8")

    @staticmethod
    def _count_atoms(path: Path) -> int:
        """统计 ATOM/HETATM 原子数。"""

        return sum(
            1
            for line in read_text_smart(path).splitlines()
            if line.startswith(("ATOM", "HETATM"))
        )

    @staticmethod
    def _to_pdbqt(clean_pdb: Path, prepared_dir: Path) -> Path:
        """转换为受体 PDBQT。"""

        pdbqt_path = prepared_dir / f"{clean_pdb.stem}.pdbqt"

        # 优先 AutoDockTools prepare_receptor4.py（若用户已安装）
        adt_script = shutil.which("prepare_receptor4.py")
        if adt_script:
            from app.utils.subprocess_runner import run_command  # noqa: PLC0415

            run_command(
                ["python", adt_script, "-r", str(clean_pdb), "-o", str(pdbqt_path), "-A", "hydrogens"],
                timeout=600,
                friendly_name="AutoDockTools 受体准备脚本",
            )
            return pdbqt_path

        # 回退 OpenBabel 刚性受体转换
        OpenBabelConverter.to_pdbqt_receptor(clean_pdb, pdbqt_path)
        return pdbqt_path
