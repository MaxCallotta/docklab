"""OpenBabel CLI 封装。

所有 OpenBabel 调用统一收敛在本模块：
- cdxml -> SDF（加氢、3D 生成）
- SDF/SMILES -> PDBQT 配体（pH 加氢 + Gasteiger 电荷）
- PDB -> PDBQT 受体（刚性受体模式）

外部依赖：OpenBabel 3.x 可执行程序（obabel）。
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import EngineExecError, EngineNotFoundError, MoleculeParseError
from app.utils.file_utils import ensure_dir
from app.utils.subprocess_runner import run_command


class OpenBabelConverter:
    """OpenBabel 静态方法集合，保持无状态、易测试。"""

    @staticmethod
    def find_obabel() -> str:
        """查找 obabel 可执行程序路径。"""

        settings = get_settings()
        if not settings.engine.obabel_bin:
            raise MoleculeParseError(
                "未找到 OpenBabel（obabel）。请安装 OpenBabel 3.x 并配置 OBABEL_BIN 环境变量。"
            )
        return settings.engine.obabel_bin

    @classmethod
    def _run(cls, command: list[str], *, friendly_name: str = "OpenBabel 分子转换器") -> None:
        """执行 obabel 命令并校验输出。"""

        try:
            run_command(
                [cls.find_obabel(), *command],
                timeout=600,
                friendly_name=friendly_name,
            )
        except (EngineExecError, EngineNotFoundError) as exc:
            raise MoleculeParseError(f"{friendly_name}执行失败：{exc.message}") from exc

    @staticmethod
    def _check_output(output_path: Path, hint: str) -> None:
        """校验转换输出文件非空。"""

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise MoleculeParseError(
                f"分子转换失败：未生成有效输出文件。{hint}"
            )

    @classmethod
    def to_sdf(
        cls,
        source: Path,
        output_sdf: Path,
        *,
        add_h: bool = True,
        gen3d: bool = True,
    ) -> Path:
        """转换为 SDF；cdxml 场景默认补氢并生成 3D 坐标。"""

        ensure_dir(output_sdf.parent)
        options: list[str] = []
        if add_h:
            options.append("-h")
        if gen3d:
            options.append("--gen3d")
        cls._run([str(source), "-O", str(output_sdf), *options])
        cls._check_output(output_sdf, "请检查 cdxml 文件是否完整或包含有效分子结构。")
        return output_sdf

    @classmethod
    def to_pdbqt_ligand(cls, source: Path, output_pdbqt: Path, *, ph: float = 7.4) -> Path:
        """生成配体 PDBQT：pH 加氢 + Gasteiger 电荷 + 3D 坐标。"""

        ensure_dir(output_pdbqt.parent)
        cls._run(
            [
                str(source),
                "-O",
                str(output_pdbqt),
                "-p",
                str(ph),
                "--partialcharge",
                "gasteiger",
                "--gen3d",
            ],
            friendly_name="OpenBabel 配体 PDBQT 生成器",
        )
        cls._check_output(output_pdbqt, "配体结构可能不含有效原子，请检查输入。")
        return output_pdbqt

    @classmethod
    def to_pdbqt_receptor(cls, source: Path, output_pdbqt: Path) -> Path:
        """生成受体 PDBQT（刚性模式，不包含可旋转键）。"""

        ensure_dir(output_pdbqt.parent)
        cls._run(
            [str(source), "-O", str(output_pdbqt), "-xr"],
            friendly_name="OpenBabel 受体 PDBQT 生成器",
        )
        cls._check_output(output_pdbqt, "受体结构可能为空，请检查 PDB 文件。")
        return output_pdbqt

    @classmethod
    def smiles_to_sdf(cls, smiles: str, output_sdf: Path, *, gen3d: bool = True) -> Path:
        """SMILES -> SDF；通过 stdin 传入，避免 shell 转义问题。"""

        ensure_dir(output_sdf.parent)
        options = ["-ismi", "-", "-O", str(output_sdf)]
        if gen3d:
            options.append("--gen3d")
        try:
            run_command(
                [cls.find_obabel(), *options],
                input_text=smiles.strip(),
                timeout=600,
                friendly_name="OpenBabel SMILES 转换器",
            )
        except (EngineExecError, EngineNotFoundError) as exc:
            raise MoleculeParseError(f"OpenBabel SMILES 转换器执行失败：{exc.message}") from exc
        cls._check_output(output_sdf, "SMILES 字符串可能无法解析为有效分子。")
        return output_sdf

    @classmethod
    def convert(cls, source: Path, output: Path) -> Path:
        """通用格式转换（按输出后缀自动推断目标格式）。"""

        ensure_dir(output.parent)
        cls._run([str(source), "-O", str(output)], friendly_name="OpenBabel 格式转换器")
        cls._check_output(output, "格式转换未生成有效输出。")
        return output
