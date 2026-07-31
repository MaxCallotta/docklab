"""RDKit 封装：结构校验、属性计算、构象生成。

RDKit 作为可选增强依赖：未安装时解析器自动降级为 OpenBabel + 轻量校验，
保证核心流程仍可运行。
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from app.core.exceptions import MoleculeValidationError
from app.utils.file_utils import ensure_dir


def rdkit_available() -> bool:
    """判断 RDKit 是否可用。"""

    return importlib.util.find_spec("rdkit") is not None


def _get_rdkit():
    """懒加载 RDKit，避免未安装时模块导入失败。"""

    if not rdkit_available():
        raise MoleculeValidationError("RDKit 未安装，无法执行 RDKit 结构校验。")
    from rdkit import Chem  # noqa: PLC0415
    return Chem


class RdkItConverter:
    """RDKit 分子处理静态工具。"""

    @staticmethod
    def _sdf_path_for_rdkit(sdf_path: Path) -> tuple[Path, Path | None]:
        """RDKit 在 Windows 上无法打开含中文等非 ASCII 字符的路径，必要时复制到 ASCII 临时文件。"""

        sdf_path = Path(sdf_path)
        if str(sdf_path).isascii():
            return sdf_path, None
        fd, tmp_name = tempfile.mkstemp(prefix="rdkit_", suffix=".sdf")
        os.close(fd)
        tmp_path = Path(tmp_name)
        shutil.copy2(sdf_path, tmp_path)
        return tmp_path, tmp_path

    @staticmethod
    def _load_mol(sdf_path: Path):
        """读取 SDF 首个分子，并修复 OpenBabel 显式价态导致的隐氢丢失。"""

        Chem = _get_rdkit()
        sdf_path, tmp_path = RdkItConverter._sdf_path_for_rdkit(sdf_path)
        try:
            text = sdf_path.read_text(encoding="utf-8", errors="replace")
            mol = Chem.MolFromMolBlock(text, sanitize=False, removeHs=False)
            if mol is None:
                supplier = Chem.SDMolSupplier(str(sdf_path), sanitize=True, removeHs=False)
                for candidate in supplier:
                    if candidate is not None:
                        mol = candidate
                        break
            if mol is None:
                return None
            try:
                for atom in mol.GetAtoms():
                    atom.SetNoImplicit(False)
                Chem.SanitizeMol(mol)
            except Exception:
                pass
            return mol
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    @staticmethod
    def smiles_to_sdf(smiles: str, output_sdf: Path, *, add_h: bool = True) -> Path:
        """SMILES -> 3D SDF（ETKDG 构象 + MMFF 优化）。"""

        Chem = _get_rdkit()
        from rdkit.Chem import AllChem  # noqa: PLC0415
        from rdkit.Chem import rdMolDescriptors  # noqa: PLC0415

        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            raise MoleculeValidationError(f"SMILES 无法解析为合法分子：{smiles.strip()}")

        mol = Chem.AddHs(mol) if add_h else mol
        params = AllChem.ETKDGv3()
        params.randomSeed = 0xC0FFEE
        if AllChem.EmbedMolecule(mol, params) != 0:
            raise MoleculeValidationError("3D 构象生成失败，请检查分子拓扑。")
        try:
            AllChem.MMFFOptimizeMolecule(mol)
        except Exception:
            pass

        ensure_dir(output_sdf.parent)
        writer = Chem.SDWriter(str(output_sdf))
        writer.write(mol)
        writer.close()
        return output_sdf

    @staticmethod
    def sdf_to_smiles(sdf_path: Path) -> str:
        """读取 SDF 第一个分子并返回规范 SMILES。"""

        Chem = _get_rdkit()
        mol = RdkItConverter._load_mol(sdf_path)
        if mol is None:
            raise MoleculeValidationError("SDF 中未找到有效分子。")
        return Chem.MolToSmiles(Chem.RemoveHs(mol))

    @staticmethod
    def compute_properties(sdf_path: Path) -> dict[str, Any]:
        """计算常见药物化学属性。"""

        Chem = _get_rdkit()
        from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors  # noqa: PLC0415

        mol = RdkItConverter._load_mol(sdf_path)
        if mol is None:
            raise MoleculeValidationError("SDF 中未找到有效分子，无法计算属性。")
        heavy = Chem.RemoveHs(mol)
        return {
            "molecular_weight": round(Descriptors.MolWt(heavy), 3),
            "logp": round(Crippen.MolLogP(heavy), 3),
            "tpsa": round(rdMolDescriptors.CalcTPSA(heavy), 3),
            "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(heavy),
            "hbd": rdMolDescriptors.CalcNumHBD(heavy),
            "hba": rdMolDescriptors.CalcNumHBA(heavy),
            "heavy_atoms": heavy.GetNumHeavyAtoms(),
        }
