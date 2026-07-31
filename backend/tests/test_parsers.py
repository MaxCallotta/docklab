"""分子解析与预处理测试。"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from app.chemistry.parsers.cdxml_parser import CdxmlParser
from app.chemistry.parsers.pdb_parser import PdbParser
from app.chemistry.parsers.registry import detect_format
from app.chemistry.prep.cdxml_preprocessor import CdxmlPreprocessor
from app.chemistry.prep.pdb_preprocessor import PdbPreprocessor


FIXTURES = Path(__file__).parent / "fixtures"


class ParserTest(unittest.TestCase):
    """格式识别与 cdxml/PDB 解析测试。"""

    def test_detect_format(self) -> None:
        """后缀自动识别格式。"""

        self.assertEqual(detect_format("x.cdxml"), "cdxml")
        self.assertEqual(detect_format("x.pdb"), "pdb")
        self.assertEqual(detect_format("x.txt"), "smiles")

    def test_pdb_parser(self) -> None:
        """PDB 解析返回原子统计。"""

        parsed = PdbParser().parse(FIXTURES / "receptor.pdb")
        self.assertEqual(parsed.num_molecules, 1)
        self.assertTrue(parsed.warnings)

    @unittest.skipUnless(shutil.which("obabel"), "需要安装 OpenBabel")
    def test_cdxml_parser(self) -> None:
        """cdxml 解析应得到 1 个分子。"""

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            result = CdxmlPreprocessor().preprocess(FIXTURES / "methane.cdxml", work)
            self.assertEqual(result.num_molecules, 1)
            self.assertIsNotNone(result.primary_path)
            self.assertTrue(result.primary_path.exists())

    @unittest.skipUnless(shutil.which("obabel"), "需要安装 OpenBabel")
    def test_cdxml_parser_via_parser_class(self) -> None:
        """CdxmlParser 返回标准化 ParsedMolecule。"""

        parsed = CdxmlParser().parse(FIXTURES / "methane.cdxml")
        self.assertEqual(parsed.num_molecules, 1)
        self.assertTrue(parsed.mol_files)

    def test_cdxml_normalizer_merges_nested_fragment(self) -> None:
        """ChemDraw 片段标签应被合并，不再保留 Fragment/ExternalConnectionPoint 节点。"""

        from app.chemistry.parsers.cdxml_normalizer import normalize_cdxml

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "flattened.cdxml"
            _, changed = normalize_cdxml(FIXTURES / "nested_fragment.cdxml", dest)
            self.assertTrue(changed)
            text = dest.read_text(encoding="utf-8")
            self.assertNotIn("NodeType=\"Fragment\"", text)
            self.assertNotIn("ExternalConnectionPoint", text)

    @unittest.skipUnless(shutil.which("obabel"), "需要安装 OpenBabel")
    def test_cdxml_nested_fragment_is_single_complete_ligand(self) -> None:
        """含外部连接点的 cdxml 应解析为单一完整配体，而非拆分/空 PDBQT。"""

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            result = CdxmlPreprocessor().preprocess(FIXTURES / "nested_fragment.cdxml", work)
            self.assertEqual(result.num_molecules, 1)
            pdbqt = result.primary_path
            self.assertIsNotNone(pdbqt)
            self.assertGreater(pdbqt.stat().st_size, 0)
            sdf_text = result.ligands[0].sdf_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            self.assertIn("C8F2NO2", sdf_text)
            props = result.ligands[0].properties
            self.assertGreaterEqual(props.get("hbd", 0), 1)
            self.assertGreaterEqual(props.get("hba", 0), 1)
            self.assertIn("C(=O)O", result.ligands[0].smiles)

    def test_rdkit_reads_non_ascii_sdf_path(self) -> None:
        """RDKit 应能读取含中文路径的 SDF 并计算属性。"""

        from app.chemistry.converters.rdkit_converter import RdkItConverter

        with tempfile.TemporaryDirectory() as tmp:
            chinese_dir = Path(tmp) / "配体"
            chinese_dir.mkdir()
            target = chinese_dir / "分子.sdf"
            shutil.copy2(FIXTURES / "ligand.sdf", target)
            props = RdkItConverter.compute_properties(target)
            self.assertGreater(props["heavy_atoms"], 0)
            self.assertGreater(props["molecular_weight"], 0)
            self.assertTrue(RdkItConverter.sdf_to_smiles(target))

    def test_pdb_preprocessor_removes_water(self) -> None:
        """受体预处理移除水分子与杂原子。"""

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            result = PdbPreprocessor().preprocess(FIXTURES / "receptor.pdb", work)
            self.assertIsNotNone(result.receptor)
            before = result.receptor.atom_count_before
            after = result.receptor.atom_count_after
            self.assertEqual(before, 36)
            self.assertLess(after, before)


if __name__ == "__main__":
    unittest.main()
