"""PmlGenerator 单元测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.visualization.pml_generator import PmlGenerator
from app.visualization.pymol_launcher import PymolLauncher


class PmlGeneratorTest(unittest.TestCase):
    """PML 脚本内容测试。"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="cadd_pml_"))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_generate_pml(self) -> None:
        """生成的 PML 包含核心渲染命令。"""

        receptor = self.tmp / "receptor.pdb"
        ligand = self.tmp / "ligand.pdbqt"
        receptor.write_text("ATOM      1  N   ALA A   1       0.000   0.000   0.000\n")
        ligand.write_text("HETATM    1  C1  LIG     1       1.000   0.000   0.000\n")

        output = self.tmp / "visualization.pml"
        PmlGenerator().export_pml(receptor, ligand, output, affinity=-8.5)
        text = output.read_text(encoding="utf-8")

        self.assertIn('load "', text)
        self.assertIn("show cartoon, receptor", text)
        self.assertIn("show sticks, ligand", text)
        self.assertIn("distance hbonds", text)
        self.assertIn("affinity = -8.50", text)

    def test_pymol_launcher_finds_executable(self) -> None:
        """本机已安装 PyMOL 时应能探测到可执行程序。"""

        launcher = PymolLauncher()
        self.assertTrue(launcher._pymol_bin)


if __name__ == "__main__":
    unittest.main()
